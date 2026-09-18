from datetime import datetime

from app.database.database import db


class NumberingService:
    def __init__(self, database=None):
        self.db = database or db

    def next_offer_number(self, year=None):
        """Atomically reserve and return the next offer number."""
        selected_year = int(year or datetime.now().year)
        with self.db.transaction(immediate=True) as conn:
            row = conn.execute(
                """SELECT last_number FROM document_sequences
                   WHERE document_type=? AND year=?""",
                ("offer", selected_year),
            ).fetchone()
            next_number = (row[0] if row else 0) + 1
            conn.execute(
                """INSERT INTO document_sequences(
                       document_type, year, last_number
                   ) VALUES (?, ?, ?)
                   ON CONFLICT(document_type, year)
                   DO UPDATE SET last_number=excluded.last_number""",
                ("offer", selected_year, next_number),
            )
        return f"P-{selected_year}-{next_number:06d}"

    def preview_offer_number(self, year=None):
        """Return the likely next number without reserving it."""
        selected_year = int(year or datetime.now().year)
        with self.db.connect() as conn:
            row = conn.execute(
                """SELECT last_number FROM document_sequences
                   WHERE document_type=? AND year=?""",
                ("offer", selected_year),
            ).fetchone()
        next_number = (row[0] if row else 0) + 1
        return f"P-{selected_year}-{next_number:06d}"


numbering_service = NumberingService()
