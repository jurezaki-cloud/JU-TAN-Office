from app.database.database import db


class OfferRepository:

    # ==========================
    # PONUDBE
    # ==========================

    def get_all(self):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.number,
                c.company,
                o.issue_date,
                o.valid_until,
                o.status,
                o.total
            FROM offers o
            LEFT JOIN customers c
                ON c.id = o.customer_id
            ORDER BY o.id DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_by_id(self, offer_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM offers
            WHERE id=?
        """, (offer_id,))

        row = cursor.fetchone()

        conn.close()

        return row

    def create(
        self,
        number,
        customer_id,
        issue_date,
        valid_until,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO offers(

                number,
                customer_id,
                issue_date,
                valid_until,
                status,

                subtotal,
                discount,
                vat,
                total,

                notes

            )
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (

            number,
            customer_id,
            issue_date,
            valid_until,
            status,

            subtotal,
            discount,
            vat,
            total,

            notes,

        ))

        conn.commit()

        offer_id = cursor.lastrowid

        conn.close()

        return offer_id

    def update(
        self,
        offer_id,
        customer_id,
        issue_date,
        valid_until,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE offers
            SET

                customer_id=?,
                issue_date=?,
                valid_until=?,
                status=?,

                subtotal=?,
                discount=?,
                vat=?,
                total=?,

                notes=?

            WHERE id=?

        """, (

            customer_id,
            issue_date,
            valid_until,
            status,

            subtotal,
            discount,
            vat,
            total,

            notes,

            offer_id,

        ))

        conn.commit()
        conn.close()

    def delete(self, offer_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM offers WHERE id=?",
            (offer_id,),
        )

        conn.commit()
        conn.close()

    # ==========================
    # POSTAVKE PONUDBE
    # ==========================

    def get_items(self, offer_id):

        conn = db.connect()
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
            FROM offer_items
            WHERE offer_id=?
            ORDER BY id
        """, (offer_id,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def add_item(
        self,
        offer_id,
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

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO offer_items(

                offer_id,
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
            VALUES(?,?,?,?,?,?,?,?,?,?,?)

        """, (

            offer_id,
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

    def delete_items(self, offer_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM offer_items WHERE offer_id=?",
            (offer_id,),
        )

        conn.commit()
        conn.close()


offer_repository = OfferRepository()