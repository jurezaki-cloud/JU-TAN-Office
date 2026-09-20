from app.database.database import db


class ArticleRepository:

    def _connect(self):
        return db.connect()

    def get_all(self):

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                code,
                name,
                unit,
                price,
                vat
            FROM articles
            ORDER BY name COLLATE NOCASE
        """)

        rows = cur.fetchall()
        conn.close()

        return rows

    def get_by_id(self, article_id):

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                code,
                name,
                description,
                unit,
                price,
                vat
            FROM articles
            WHERE id=?
        """, (article_id,))

        row = cur.fetchone()
        conn.close()

        return row

    def code_exists(self, code, exclude_id=None):

        conn = self._connect()
        cur = conn.cursor()

        if exclude_id is None:
            cur.execute(
                "SELECT id FROM articles WHERE code=?",
                (code,),
            )
        else:
            cur.execute("""
                SELECT id
                FROM articles
                WHERE code=? AND id<>?
            """, (
                code,
                exclude_id,
            ))

        exists = cur.fetchone() is not None

        conn.close()

        return exists

    def add(
        self,
        code,
        name,
        description,
        unit,
        price,
        vat,
    ):

        if self.code_exists(code):
            raise ValueError("Šifra artikla že obstaja.")

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO articles(
                code,
                name,
                description,
                unit,
                price,
                vat
            )
            VALUES (?,?,?,?,?,?)
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

        if self.code_exists(code, article_id):
            raise ValueError("Šifra artikla že obstaja.")

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            UPDATE articles
            SET
                code=?,
                name=?,
                description=?,
                unit=?,
                price=?,
                vat=?
            WHERE id=?
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

        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM articles WHERE id=?",
            (article_id,),
        )

        conn.commit()
        conn.close()

    def search(self, text):

        conn = self._connect()
        cur = conn.cursor()

        text = f"%{text}%"

        cur.execute("""
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
            ORDER BY name COLLATE NOCASE
        """, (
            text,
            text,
        ))

        rows = cur.fetchall()

        conn.close()

        return rows

    def get_next_code(self):

        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT code
            FROM articles
            WHERE code LIKE 'ART%'
            ORDER BY CAST(SUBSTR(code,4) AS INTEGER) DESC
            LIMIT 1
        """)

        row = cur.fetchone()

        conn.close()

        if row is None:
            return "ART0001"

        try:
            number = int(row[0][3:])
        except (ValueError, TypeError):
            number = 0

        return f"ART{number + 1:04d}"

    def list_page(self, text: str = "", *, limit: int = 200, offset: int = 0):
        """Stran seznama (LIMIT) — obstoječi search/get_all ostanejo."""
        from app.core.search_engine import fts_available, fts_query

        conn = self._connect()
        cur = conn.cursor()
        limit = max(1, int(limit))
        offset = max(0, int(offset))
        needle = (text or "").strip()
        if needle and fts_available():
            match = fts_query(needle)
            if match:
                try:
                    cur.execute(
                        """
                        SELECT a.id, a.code, a.name, a.unit, a.price, a.vat
                        FROM articles_fts f
                        JOIN articles a ON a.id = f.rowid
                        WHERE articles_fts MATCH ?
                        ORDER BY a.name COLLATE NOCASE
                        LIMIT ? OFFSET ?
                        """,
                        (match, limit, offset),
                    )
                    rows = cur.fetchall()
                    conn.close()
                    return rows
                except Exception:
                    pass
        if needle:
            like = f"%{needle}%"
            cur.execute(
                """
                SELECT id, code, name, unit, price, vat
                FROM articles
                WHERE code LIKE ? OR name LIKE ?
                ORDER BY name COLLATE NOCASE
                LIMIT ? OFFSET ?
                """,
                (like, like, limit, offset),
            )
        else:
            cur.execute(
                """
                SELECT id, code, name, unit, price, vat
                FROM articles
                ORDER BY name COLLATE NOCASE
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        rows = cur.fetchall()
        conn.close()
        return rows


article_repository = ArticleRepository()