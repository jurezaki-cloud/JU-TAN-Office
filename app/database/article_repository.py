from app.core.validation import (
    money_for_storage,
    optional_text,
    percentage_for_storage,
    required_text,
)
from app.database.database import db


class ArticleRepository:
    def __init__(self, database=None):
        self.db = database or db

    @staticmethod
    def _validated_data(code, name, description, unit, price, vat):
        return (
            required_text(code, "Šifra", 50).upper(),
            required_text(name, "Naziv"),
            optional_text(description, "Opis", 2000),
            required_text(unit, "Enota", 30),
            money_for_storage(price, "Cena"),
            percentage_for_storage(vat, "DDV"),
        )

    def get_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, code, name, unit, price, vat
                   FROM articles ORDER BY name"""
            ).fetchall()

    def get_by_id(self, article_id):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, code, name, description, unit, price, vat
                   FROM articles WHERE id = ?""",
                (article_id,),
            ).fetchone()

    def add(self, code, name, description, unit, price, vat):
        values = self._validated_data(code, name, description, unit, price, vat)
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO articles(code, name, description, unit, price, vat)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                values,
            )
            return cursor.lastrowid

    def update(self, article_id, code, name, description, unit, price, vat):
        values = self._validated_data(code, name, description, unit, price, vat)
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """UPDATE articles
                   SET code=?, name=?, description=?, unit=?, price=?, vat=?
                   WHERE id=?""",
                (*values, article_id),
            )
            if cursor.rowcount == 0:
                raise LookupError("Artikel ne obstaja.")

    def delete(self, article_id):
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM articles WHERE id=?", (article_id,)
            )
            if cursor.rowcount == 0:
                raise LookupError("Artikel ne obstaja.")

    def search(self, text):
        pattern = f"%{optional_text(text, 'Iskanje', 200)}%"
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, code, name, unit, price, vat
                   FROM articles
                   WHERE code LIKE ? OR name LIKE ? ORDER BY name""",
                (pattern, pattern),
            ).fetchall()

    def get_next_code(self):
        with self.db.connect() as conn:
            row = conn.execute(
                """SELECT code FROM articles WHERE code LIKE 'ART%'
                   ORDER BY CAST(SUBSTR(code, 4) AS INTEGER) DESC LIMIT 1"""
            ).fetchone()
        if not row or not row[0]:
            return "ART0001"
        try:
            number = int(row[0][3:])
        except (ValueError, IndexError):
            number = 0
        return f"ART{number + 1:04d}"


article_repository = ArticleRepository()
