from datetime import datetime

from app.database.database import db


class NumberingService:

    def next_offer_number(self):

        year = datetime.now().year

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT number
            FROM offers
            WHERE number LIKE ?
            ORDER BY id DESC
            LIMIT 1
        """, (f"P-{year}-%",))

        row = cursor.fetchone()

        conn.close()

        if row is None:
            return f"P-{year}-000001"

        last = row[0]

        try:
            number = int(last.split("-")[-1]) + 1
        except Exception:
            number = 1

        return f"P-{year}-{number:06d}"


numbering_service = NumberingService()