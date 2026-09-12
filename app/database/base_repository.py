import re

from app.database.database import db

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(name: str) -> str:
    """Dovoli samo SQL identifikatorje (zaščita pred injekcijo)."""
    if not _IDENTIFIER.match(name or ""):
        raise ValueError("Neveljavno ime tabele ali stolpca.")
    return name


class BaseRepository:
    """Osnovni CRUD z vezanimi parametri in preverjenimi identifikatorji."""

    table = None
    order_by = "id"

    def get_all(self):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {_ident(self.table)} ORDER BY {_ident(self.order_by)}"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_by_id(self, row_id):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {_ident(self.table)} WHERE id=?",
            (row_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def delete(self, row_id):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {_ident(self.table)} WHERE id=?",
            (row_id,),
        )
        conn.commit()
        conn.close()

    def search(self, field, text):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT *
            FROM {_ident(self.table)}
            WHERE {_ident(field)} LIKE ?
            ORDER BY {_ident(self.order_by)}
            """,
            (f"%{text}%",),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows
