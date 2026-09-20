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

        cursor.execute("""
            SELECT *
            FROM invoices
            WHERE id=?
        """, (invoice_id,))

        row = cursor.fetchone()

        conn.close()

        return row

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

    def get_next_number(self):
        """Next invoice number, never colliding with existing RAC-* rows."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                invoice_prefix,
                invoice_counter
            FROM company
            WHERE id=1
        """)
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

        if highest != counter:
            cursor.execute(
                "UPDATE company SET invoice_counter=? WHERE id=1",
                (highest,),
            )
            conn.commit()
            counter = highest

        conn.close()
        return f"{prefix}-{counter:04d}"

    def increase_counter(self):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE company
            SET invoice_counter = invoice_counter + 1
            WHERE id=1
        """)

        conn.commit()
        conn.close()

    def allocate_next_number(self) -> str:
        """Atomically peek+bump so two open dialogs cannot share one number."""
        number = self.get_next_number()
        self.increase_counter()
        return number

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
    ):
        from app.utils.vat import company_vat_liable, vat_liable_int

        self.ensure_schema()
        if vat_liable is None:
            vat_liable = company_vat_liable()

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO invoices(
                invoice_number,
                customer_id,
                issue_date,
                due_date,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            invoice_number,
            customer_id,
            issue_date,
            due_date,
            status,
            subtotal,
            discount,
            vat,
            total,
            notes,
            vat_liable_int(vat_liable),
        ))

        conn.commit()

        invoice_id = cursor.lastrowid

        conn.close()

        return invoice_id

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
    ):
        from app.utils.vat import vat_liable_int

        self.ensure_schema()
        if vat_liable is None:
            vat_liable = self.get_vat_liable(invoice_id)

        conn = self._connect()
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

        conn.commit()
        conn.close()

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

        new_id = self.add(
            invoice_number=self.get_next_number(),
            customer_id=invoice[2],
            issue_date=invoice[3],
            due_date=invoice[4],
            subtotal=invoice[6],
            discount=invoice[7],
            vat=invoice[8],
            total=invoice[9],
            notes=invoice[10],
            status="Osnutek",
            vat_liable=self.get_vat_liable(invoice_id),
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
            )

        self.increase_counter()

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
    ):

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

    def delete_items(self, invoice_id):

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM invoice_items WHERE invoice_id=?",
            (invoice_id,),
        )

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