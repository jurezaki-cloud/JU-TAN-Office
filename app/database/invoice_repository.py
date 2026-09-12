from app.database.database import db


class InvoiceRepository:

    def _connect(self):
        return db.connect()

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

        conn.close()

        prefix = (row[0] if row and row[0] else "RAC")
        counter = int(row[1] if row and row[1] is not None else 1)

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
    ):

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
                notes
            )
            VALUES (?,?,?,?,?,?,?,?,?,?)
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
    ):

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
                notes=?
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

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COALESCE(SUM(price * quantity),0),
                COALESCE(SUM((price * quantity) * discount / 100),0),
                COALESCE(SUM(total - ((price * quantity) - ((price * quantity) * discount / 100))),0),
                COALESCE(SUM(total),0)
            FROM invoice_items
            WHERE invoice_id=?
        """, (invoice_id,))

        subtotal, discount, vat, total = cursor.fetchone()

        cursor.execute("""
            UPDATE invoices
            SET
                subtotal=?,
                discount=?,
                vat=?,
                total=?
            WHERE id=?
        """, (
            subtotal,
            discount,
            vat,
            total,
            invoice_id,
        ))

        conn.commit()
        conn.close()

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