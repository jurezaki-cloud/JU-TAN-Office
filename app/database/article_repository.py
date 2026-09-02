from app.database.database import db


class ArticleRepository:

    def get_all(self):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                code,
                name,
                unit,
                price,
                vat
            FROM articles
            ORDER BY name
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_by_id(self, article_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                code,
                name,
                description,
                unit,
                price,
                vat
            FROM articles
            WHERE id = ?
        """, (article_id,))

        row = cursor.fetchone()

        conn.close()

        return row

    def add(
        self,
        code,
        name,
        description,
        unit,
        price,
        vat,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO articles(
                code,
                name,
                description,
                unit,
                price,
                vat
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            description,
            unit,
            price,
            vat,
        ))

        conn.commit()
        conn.close()

    def update(
        self,
        article_id,
        code,
        name,
        description,
        unit,
        price,
        vat,
    ):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE articles
            SET
                code = ?,
                name = ?,
                description = ?,
                unit = ?,
                price = ?,
                vat = ?
            WHERE id = ?
        """, (
            code,
            name,
            description,
            unit,
            price,
            vat,
            article_id,
        ))

        conn.commit()
        conn.close()

    def delete(self, article_id):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM articles WHERE id = ?",
            (article_id,),
        )

        conn.commit()
        conn.close()

    def search(self, text):

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                code,
                name,
                unit,
                price,
                vat
            FROM articles
            WHERE
                code LIKE ?
                OR name LIKE ?
            ORDER BY name
        """, (
            f"%{text}%",
            f"%{text}%",
        ))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_next_code(self):
        """
        Vrne naslednjo šifro artikla v obliki:
        ART0001
        ART0002
        ART0003
        """

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code
            FROM articles
            WHERE code LIKE 'ART%'
            ORDER BY CAST(SUBSTR(code, 4) AS INTEGER) DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

        conn.close()

        if row is None or row[0] is None:
            return "ART0001"

        try:
            number = int(row[0][3:])
        except (ValueError, IndexError):
            number = 0

        return f"ART{number + 1:04d}"


article_repository = ArticleRepository()