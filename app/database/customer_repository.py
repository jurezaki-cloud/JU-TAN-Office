from app.database.database import db


class CustomerRepository:

    def get_all(self):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                company,
                contact,
                phone,
                email,
                city
            FROM customers
            ORDER BY company
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_by_id(self, customer_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company,
                contact,
                address,
                postal_code,
                city,
                country,
                tax_number,
                email,
                phone
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        )

        row = cursor.fetchone()

        conn.close()

        return row

    def add(
        self,
        company,
        contact,
        address,
        postal_code,
        city,
        country,
        tax_number,
        email,
        phone,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO customers(
                company,
                contact,
                address,
                postal_code,
                city,
                country,
                tax_number,
                email,
                phone
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                company,
                contact,
                address,
                postal_code,
                city,
                country,
                tax_number,
                email,
                phone,
            ),
        )

        conn.commit()
        conn.close()

    def update(
        self,
        customer_id,
        company,
        contact,
        address,
        postal_code,
        city,
        country,
        tax_number,
        email,
        phone,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE customers
            SET
                company=?,
                contact=?,
                address=?,
                postal_code=?,
                city=?,
                country=?,
                tax_number=?,
                email=?,
                phone=?
            WHERE id=?
            """,
            (
                company,
                contact,
                address,
                postal_code,
                city,
                country,
                tax_number,
                email,
                phone,
                customer_id,
            ),
        )

        conn.commit()
        conn.close()

    def delete(self, customer_id):

        conn = db.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM customers WHERE id=?",
                (customer_id,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def search(self, text):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                company,
                contact,
                phone,
                email,
                city
            FROM customers
            WHERE
                company LIKE ?
                OR contact LIKE ?
                OR city LIKE ?
            ORDER BY company
            """,
            (
                f"%{text}%",
                f"%{text}%",
                f"%{text}%",
            ),
        )

        rows = cursor.fetchall()

        conn.close()

        return rows

    def list_page(self, text: str = "", *, limit: int = 200, offset: int = 0):
        from app.core.search_engine import fts_available, fts_query

        conn = db.connect()
        cursor = conn.cursor()
        limit = max(1, int(limit))
        offset = max(0, int(offset))
        needle = (text or "").strip()
        if needle and fts_available():
            match = fts_query(needle)
            if match:
                try:
                    cursor.execute(
                        """
                        SELECT c.id, c.company, c.contact, c.phone, c.email, c.city
                        FROM customers_fts f
                        JOIN customers c ON c.id = f.rowid
                        WHERE customers_fts MATCH ?
                        ORDER BY c.company
                        LIMIT ? OFFSET ?
                        """,
                        (match, limit, offset),
                    )
                    rows = cursor.fetchall()
                    conn.close()
                    return rows
                except Exception:
                    pass
        if needle:
            like = f"%{needle}%"
            cursor.execute(
                """
                SELECT id, company, contact, phone, email, city
                FROM customers
                WHERE company LIKE ? OR contact LIKE ? OR city LIKE ?
                ORDER BY company
                LIMIT ? OFFSET ?
                """,
                (like, like, like, limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT id, company, contact, phone, email, city
                FROM customers
                ORDER BY company
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = cursor.fetchall()
        conn.close()
        return rows


customer_repository = CustomerRepository()