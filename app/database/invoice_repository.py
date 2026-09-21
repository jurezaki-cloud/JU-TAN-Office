from app.database.database import db


class InvoiceRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        """Add vat_liable snapshot column without rewriting existing invoices."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'"
        )
        if cursor.fetchone():
            cols = {
                row[1]
                for row in cursor.execute("PRAGMA table_info(invoices)").fetchall()
            }
            if "vat_liable" not in cols:
                cursor.execute(
                    "ALTER TABLE invoices ADD COLUMN vat_liable INTEGER DEFAULT 1"
                )
                cursor.execute(
                    "UPDATE invoices SET vat_liable=1 WHERE vat_liable IS NULL"
                )
        conn.commit()
        conn.close()

    def get_vat_liable(self, invoice_id) -> bool:
        from app.utils.vat import parse_vat_liable

        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT vat_liable FROM invoices WHERE id=?", (invoice_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return True
        return parse_vat_liable(row[0])

    # =====================================================
    # RAČUNI
    # =====================================================

    def get_all(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.id,
                i.invoice_number,
                i.issue_date,
                c.company,
                i.total,
                i.status
            FROM invoices i
            LEFT JOIN customers c
                ON c.id = i.customer_id
            ORDER BY i.id DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_by_id(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        # Never rely on physical SQLite column order. Older Phase-8 databases
        # have a different invoices layout; return the canonical Office tuple.
        cursor.execute("""
            SELECT
                id, invoice_number, customer_id, issue_date, due_date, status,
                subtotal, discount, vat, total, notes, vat_liable, created_at
            FROM invoices
            WHERE id=?
        """, (invoice_id,))

        row = cursor.fetchone()

        conn.close()

        return row

    def get_due_dates_map(self, invoice_ids=None) -> dict:
        """Return ``{invoice_id: due_date}`` in a single query (dashboard N+1 fix).

        When *invoice_ids* is ``None``, every invoice is included. An empty
        iterable yields ``{}`` without hitting the database.
        """
        conn = self._connect()
        cursor = conn.cursor()
        if invoice_ids is None:
            cursor.execute("SELECT id, due_date FROM invoices")
        else:
            ids = []
            seen = set()
            for raw in invoice_ids:
                if raw is None:
                    continue
                try:
                    invoice_id = int(raw)
                except (TypeError, ValueError):
                    continue
                if invoice_id in seen:
                    continue
                seen.add(invoice_id)
                ids.append(invoice_id)
            if not ids:
                conn.close()
                return {}
            placeholders = ",".join("?" * len(ids))
            cursor.execute(
                f"SELECT id, due_date FROM invoices WHERE id IN ({placeholders})",
                ids,
            )
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def search(self, text):

        conn = self._connect()
        cursor = conn.cursor()

        like = f"%{text}%"

        cursor.execute("""
            SELECT
                i.id,
                i.invoice_number,
                i.issue_date,
                c.company,
                i.total,
                i.status
            FROM invoices i
            LEFT JOIN customers c
                ON c.id = i.customer_id
            WHERE
                i.invoice_number LIKE ?
                OR IFNULL(c.company, '') LIKE ?
            ORDER BY i.id DESC
        """, (like, like))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def _next_counter_on_conn(self, conn) -> tuple[str, int]:
        """Compute next free (prefix, counter) under an open write lock."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT invoice_prefix, invoice_counter
            FROM company
            WHERE id=1
            """
        )
        row = cursor.fetchone()
        prefix = (row[0] if row and row[0] else "RAC")
        counter = int(row[1] if row and row[1] is not None else 1)

        # Settings can overwrite invoice_counter downward; lift to max existing + 1.
        cursor.execute(
            """
            SELECT invoice_number FROM invoices
            WHERE invoice_number LIKE ?
            """,
            (f"{prefix}-%",),
        )
        highest = counter
        for (number,) in cursor.fetchall():
            try:
                suffix = str(number).rsplit("-", 1)[-1]
                highest = max(highest, int(suffix) + 1)
            except (TypeError, ValueError):
                continue
        return prefix, highest

    def get_next_number(self):
        """Peek next invoice number (may heal counter); does not consume it."""
        with db.transaction(immediate=True) as conn:
            prefix, counter = self._next_counter_on_conn(conn)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT invoice_counter FROM company WHERE id=1"
            )
            row = cursor.fetchone()
            stored = int(row[0] if row and row[0] is not None else 1)
            if counter != stored:
                cursor.execute(
                    "UPDATE company SET invoice_counter=? WHERE id=1",
                    (counter,),
                )
            return f"{prefix}-{counter:04d}"

    def increase_counter(self):
        with db.transaction(immediate=True) as conn:
            conn.cursor().execute(
                """
                UPDATE company
                SET invoice_counter = invoice_counter + 1
                WHERE id=1
                """
            )

    def allocate_next_number(self, conn=None) -> str:
        """Atomically reserve the next invoice number (BEGIN IMMEDIATE).

        When *conn* is provided, allocation joins that outer transaction and
        does not commit (used by offer→invoice conversion).
        """
        if conn is not None:
            return self._allocate_on_conn(conn)
        with db.transaction(immediate=True) as txn:
            return self._allocate_on_conn(txn)

    def _allocate_on_conn(self, conn) -> str:
        prefix, counter = self._next_counter_on_conn(conn)
        conn.cursor().execute(
            "UPDATE company SET invoice_counter=? WHERE id=1",
            (counter + 1,),
        )
        return f"{prefix}-{counter:04d}"

    def add(
        self,
        invoice_number,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        notes,
        status="Osnutek",
        vat_liable=None,
        conn=None,
    ):
        from app.utils.vat import company_vat_liable, vat_liable_int

        if conn is None:
            self.ensure_schema()

        owns = conn is None
        if vat_liable is None:
            # Never read company inside an outer txn: company reads commit on the
            # pooled connection and would finalize the caller's BEGIN early.
            if owns:
                vat_liable = company_vat_liable()
            else:
                vat_liable = True
        if owns:
            conn = self._connect()
        cursor = conn.cursor()

        columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(invoices)").fetchall()
        }
        # Phase-8 databases still contain a NOT NULL legacy `number` column.
        # Dual-write it when present so upgrades can create invoices safely.
        if "number" in columns:
            cursor.execute("""
                INSERT INTO invoices(
                    number, invoice_number, customer_id, issue_date, due_date,
                    status, subtotal, discount, vat, total, notes, vat_liable
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                invoice_number, invoice_number, customer_id, issue_date, due_date,
                status, subtotal, discount, vat, total, notes,
                vat_liable_int(vat_liable),
            ))
        else:
            cursor.execute("""
                INSERT INTO invoices(
                    invoice_number, customer_id, issue_date, due_date, status,
                    subtotal, discount, vat, total, notes, vat_liable
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (
                invoice_number, customer_id, issue_date, due_date, status,
                subtotal, discount, vat, total, notes,
                vat_liable_int(vat_liable),
            ))

        invoice_id = cursor.lastrowid
        if owns:
            conn.commit()
            conn.close()

        return invoice_id

    @staticmethod
    def _validate_create(customer_id, items) -> None:
        if not customer_id:
            raise ValueError("Stranka je obvezna.")
        if not items:
            raise ValueError("Dokument mora vsebovati vsaj eno postavko.")
        for item in items:
            if not str(item.get("name") or "").strip():
                raise ValueError("Postavka mora imeti naziv.")
            if float(item.get("quantity") or 0) <= 0:
                raise ValueError("Količina postavke mora biti večja od 0.")

    def create_with_items(
        self,
        *,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        notes,
        items,
        status="Izdan",
        vat_liable=None,
        invoice_number=None,
    ) -> tuple[int, str]:
        """Allocate number + insert invoice header and items in one transaction."""
        from app.utils.vat import company_vat_liable

        self.ensure_schema()
        self._validate_create(customer_id, items)
        # Resolve VAT regime before BEGIN — company reads commit on the pooled
        # connection and must not run inside the create transaction.
        if vat_liable is None:
            vat_liable = company_vat_liable()

        with db.transaction(immediate=True) as conn:
            number = invoice_number or self.allocate_next_number(conn)
            invoice_id = self.add(
                invoice_number=number,
                customer_id=customer_id,
                issue_date=issue_date,
                due_date=due_date,
                subtotal=subtotal,
                discount=discount,
                vat=vat,
                total=total,
                notes=notes,
                status=status,
                vat_liable=vat_liable,
                conn=conn,
            )
            for item in items:
                self.add_item(
                    invoice_id=invoice_id,
                    article_id=item.get("article_id"),
                    code=item.get("code") or "",
                    name=item.get("name") or "",
                    description=item.get("description") or "",
                    quantity=item.get("quantity"),
                    unit=item.get("unit") or "",
                    price=item.get("price"),
                    discount=item.get("discount") or 0,
                    vat=item.get("vat") or 0,
                    total=item.get("total"),
                    conn=conn,
                )
            counted = conn.execute(
                "SELECT COUNT(*) FROM invoice_items WHERE invoice_id=?",
                (invoice_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke računa niso bile shranjene.")
            return invoice_id, number

    def update(
        self,
        invoice_id,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        status,
        notes,
        vat_liable=None,
        conn=None,
    ):
        from app.utils.vat import vat_liable_int

        owns = conn is None
        if owns:
            self.ensure_schema()
            if vat_liable is None:
                vat_liable = self.get_vat_liable(invoice_id)
            conn = self._connect()
        elif vat_liable is None:
            raise ValueError("vat_liable je obvezen znotraj zunanje transakcije.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE invoices
            SET
                customer_id=?,
                issue_date=?,
                due_date=?,
                subtotal=?,
                discount=?,
                vat=?,
                total=?,
                status=?,
                notes=?,
                vat_liable=?
            WHERE id=?
        """, (
            customer_id,
            issue_date,
            due_date,
            subtotal,
            discount,
            vat,
            total,
            status,
            notes,
            vat_liable_int(vat_liable),
            invoice_id,
        ))

        if owns:
            conn.commit()
            conn.close()

    def update_with_items(
        self,
        invoice_id,
        *,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        status,
        notes,
        items,
        vat_liable=None,
    ) -> None:
        """Update header + replace items in one transaction (GOLD-3B)."""
        self.ensure_schema()
        self._validate_create(customer_id, items)
        if vat_liable is None:
            vat_liable = self.get_vat_liable(invoice_id)

        with db.transaction(immediate=True) as conn:
            self.update(
                invoice_id=invoice_id,
                customer_id=customer_id,
                issue_date=issue_date,
                due_date=due_date,
                subtotal=subtotal,
                discount=discount,
                vat=vat,
                total=total,
                status=status,
                notes=notes,
                vat_liable=vat_liable,
                conn=conn,
            )
            self.delete_items(invoice_id, conn=conn)
            for item in items:
                self.add_item(
                    invoice_id=invoice_id,
                    article_id=item.get("article_id"),
                    code=item.get("code") or "",
                    name=item.get("name") or "",
                    description=item.get("description") or "",
                    quantity=item.get("quantity"),
                    unit=item.get("unit") or "",
                    price=item.get("price"),
                    discount=item.get("discount") or 0,
                    vat=item.get("vat") or 0,
                    total=item.get("total"),
                    conn=conn,
                )
            counted = conn.execute(
                "SELECT COUNT(*) FROM invoice_items WHERE invoice_id=?",
                (invoice_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke računa niso bile shranjene.")

    def delete(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM invoice_items WHERE invoice_id=?",
            (invoice_id,),
        )

        cursor.execute(
            "DELETE FROM invoices WHERE id=?",
            (invoice_id,),
        )

        conn.commit()
        conn.close()

    def cancel(self, invoice_id):
        """Preserve the invoice and its ledger; mark it cancelled instead of deleting it."""
        self.update_status(invoice_id, "Storniran")

    def mark_paid(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status='Plačan'
            WHERE id=?
        """, (invoice_id,))

        conn.commit()
        conn.close()

        try:
            from app.database.payment_repository import payment_repository

            invoice = self.get_by_id(invoice_id)
            if invoice is None:
                return
            total = float(invoice[9] or 0)
            remaining = payment_repository.remaining(invoice_id, total)
            if remaining > 0:
                from datetime import date

                payment_repository.add(
                    invoice_id,
                    date.today().isoformat(),
                    remaining,
                    "Nakazilo",
                    "mark_paid",
                )
            payment_repository.sync_invoice_status(invoice_id, total)
        except Exception:
            pass

    def mark_draft(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status='Osnutek'
            WHERE id=?
        """, (invoice_id,))

        conn.commit()
        conn.close()

    def mark_sent(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status='Izdan'
            WHERE id=?
        """, (invoice_id,))

        conn.commit()
        conn.close()

    def get_last_invoices(self, limit=10):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                invoice_number,
                issue_date,
                total,
                status
            FROM invoices
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_open_invoices(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                invoice_number,
                issue_date,
                total,
                status
            FROM invoices
            WHERE status IN ('Osnutek','Izdan')
            ORDER BY issue_date DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_total_revenue(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(total),0)
            FROM invoices
            WHERE status <> 'Storniran'
        """)

        total = cursor.fetchone()[0]

        conn.close()

        return total

    def duplicate(self, invoice_id):
        """Kopira račun in postavke z novo številko kot osnutek."""

        invoice = self.get_by_id(invoice_id)

        if invoice is None:
            return None

        items = self.get_items(invoice_id)
        vat_liable = self.get_vat_liable(invoice_id)

        with db.transaction(immediate=True) as conn:
            number = self.allocate_next_number(conn)
            new_id = self.add(
                invoice_number=number,
                customer_id=invoice[2],
                issue_date=invoice[3],
                due_date=invoice[4],
                subtotal=invoice[6],
                discount=invoice[7],
                vat=invoice[8],
                total=invoice[9],
                notes=invoice[10],
                status="Osnutek",
                vat_liable=vat_liable,
                conn=conn,
            )

            for item in items:
                self.add_item(
                    invoice_id=new_id,
                    article_id=item[1],
                    code=item[2],
                    name=item[3],
                    description=item[4],
                    quantity=item[5],
                    unit=item[6],
                    price=item[7],
                    discount=item[8],
                    vat=item[9],
                    total=item[10],
                    conn=conn,
                )

        return new_id

    # =====================================================
    # POSTAVKE RAČUNA
    # =====================================================

    def add_item(
        self,
        invoice_id,
        article_id,
        code,
        name,
        description,
        quantity,
        unit,
        price,
        discount,
        vat,
        total,
        conn=None,
    ):

        owns = conn is None
        if owns:
            conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO invoice_items(
                invoice_id,
                article_id,
                code,
                name,
                description,
                quantity,
                unit,
                price,
                discount,
                vat,
                total
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            invoice_id,
            article_id,
            code,
            name,
            description,
            quantity,
            unit,
            price,
            discount,
            vat,
            total,
        ))

        if owns:
            conn.commit()
            conn.close()

    def update_item(
        self,
        item_id,
        description,
        quantity,
        unit,
        price,
        discount,
        vat,
        total,
    ):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoice_items
            SET
                description=?,
                quantity=?,
                unit=?,
                price=?,
                discount=?,
                vat=?,
                total=?
            WHERE id=?
        """, (
            description,
            quantity,
            unit,
            price,
            discount,
            vat,
            total,
            item_id,
        ))

        conn.commit()
        conn.close()

    def delete_item(self, item_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM invoice_items WHERE id=?",
            (item_id,),
        )

        conn.commit()
        conn.close()

    def delete_items(self, invoice_id, conn=None):
        owns = conn is None
        if owns:
            conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM invoice_items WHERE invoice_id=?",
            (invoice_id,),
        )
        if owns:
            conn.commit()
            conn.close()

    def get_items(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                article_id,
                code,
                name,
                description,
                quantity,
                unit,
                price,
                discount,
                vat,
                total
            FROM invoice_items
            WHERE invoice_id=?
            ORDER BY id
        """, (invoice_id,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    # =====================================================
    # IZRAČUNI
    # =====================================================

    def recalculate_totals(self, invoice_id):
        from app.utils.money import document_totals

        items = self.get_items(invoice_id)
        lines = [
            {
                "quantity": row[5],
                "price": row[7],
                "discount": row[8] or 0,
                "vat": row[9],
            }
            for row in items
        ]
        totals = document_totals(lines)

        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE invoices
            SET subtotal=?, discount=?, vat=?, total=?
            WHERE id=?
            """,
            (
                totals["subtotal"],
                totals["discount"],
                totals["vat"],
                totals["total"],
                invoice_id,
            ),
        )
        conn.commit()
        conn.close()
        return totals

    # =====================================================
    # DASHBOARD / ANALITIKA
    # =====================================================

    def count(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM invoices
        """)

        total = cursor.fetchone()[0]

        conn.close()

        return total

    def get_statistics(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(total),0),
                COALESCE(AVG(total),0),
                COALESCE(MAX(total),0)
            FROM invoices
            WHERE status <> 'Storniran'
        """)

        stats = cursor.fetchone()

        conn.close()

        return stats

    def get_monthly_revenue(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                substr(issue_date,1,7) AS month,
                COALESCE(SUM(total),0)
            FROM invoices
            WHERE status <> 'Storniran'
            GROUP BY month
            ORDER BY month
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_customer_revenue(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.company,
                COUNT(i.id),
                COALESCE(SUM(i.total),0)
            FROM invoices i
            JOIN customers c
                ON c.id=i.customer_id
            GROUP BY c.company
            ORDER BY SUM(i.total) DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_biggest_invoices(self, limit=10):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                invoice_number,
                issue_date,
                total
            FROM invoices
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def invoice_exists(self, invoice_number):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id
            FROM invoices
            WHERE invoice_number=?
        """, (invoice_number,))

        row = cursor.fetchone()

        conn.close()

        return row is not None

    def customer_has_invoices(self, customer_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM invoices
            WHERE customer_id=?
        """, (customer_id,))

        count = cursor.fetchone()[0]

        conn.close()

        return count > 0

    def get_invoice_total(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT total
            FROM invoices
            WHERE id=?
        """, (invoice_id,))

        row = cursor.fetchone()

        conn.close()

        if row:
            return row[0]

        return 0

    def update_notes(self, invoice_id, notes):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET notes=?
            WHERE id=?
        """, (
            notes,
            invoice_id,
        ))

        conn.commit()
        conn.close()

    def update_status(self, invoice_id, status):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE invoices
            SET status=?
            WHERE id=?
        """, (
            status,
            invoice_id,
        ))

        conn.commit()
        conn.close()

    def list_page(self, text: str = "", *, limit: int = 200, offset: int = 0):
        conn = self._connect()
        cursor = conn.cursor()
        limit = max(1, int(limit))
        offset = max(0, int(offset))
        needle = (text or "").strip()
        if needle:
            like = f"%{needle}%"
            cursor.execute(
                """
                SELECT
                    i.id, i.invoice_number, i.issue_date, c.company,
                    i.total, i.status, i.due_date
                FROM invoices i
                LEFT JOIN customers c ON c.id = i.customer_id
                WHERE i.invoice_number LIKE ? OR IFNULL(c.company, '') LIKE ?
                ORDER BY i.id DESC
                LIMIT ? OFFSET ?
                """,
                (like, like, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT
                    i.id, i.invoice_number, i.issue_date, c.company,
                    i.total, i.status, i.due_date
                FROM invoices i
                LEFT JOIN customers c ON c.id = i.customer_id
                ORDER BY i.id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = cursor.fetchall()
        conn.close()
        return rows


invoice_repository = InvoiceRepository()