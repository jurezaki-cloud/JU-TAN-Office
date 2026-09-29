from __future__ import annotations

from datetime import date

from app.database.database import db


class ReminderRepository:
    def ensure_schema(self) -> None:
        conn = db.connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 3),
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                recipient TEXT,
                subject TEXT,
                remaining REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_reminders_invoice ON payment_reminders(invoice_id)")
        conn.commit()
        conn.close()

    def add(self, invoice_id: int, level: int, recipient: str, subject: str, remaining: float) -> int:
        self.ensure_schema()
        if int(level) not in (1, 2, 3):
            raise ValueError("Stopnja opomina mora biti 1, 2 ali 3.")
        conn = db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO payment_reminders(invoice_id, level, recipient, subject, remaining) VALUES (?,?,?,?,?)",
            (int(invoice_id), int(level), recipient, subject, float(remaining or 0)),
        )
        conn.commit()
        reminder_id = int(cur.lastrowid)
        conn.close()
        return reminder_id

    def list_for_invoice(self, invoice_id: int):
        self.ensure_schema()
        conn = db.connect()
        rows = conn.execute(
            "SELECT id, level, sent_at, recipient, subject, remaining FROM payment_reminders WHERE invoice_id=? ORDER BY id DESC",
            (int(invoice_id),),
        ).fetchall()
        conn.close()
        return rows

    def summary(self, invoice_id: int) -> dict:
        rows = self.list_for_invoice(invoice_id)
        if not rows:
            return {"count": 0, "last_level": 0, "last_sent": "", "next_level": 1}
        last = rows[0]
        last_level = int(last[1] or 0)
        return {
            "count": len(rows),
            "last_level": last_level,
            "last_sent": str(last[2] or ""),
            "next_level": min(3, last_level + 1),
        }

    def suggested_level(self, invoice_id: int, due_date=None) -> int:
        summary = self.summary(invoice_id)
        # Opomini vedno napredujejo zaporedno: 1 -> 2 -> 3.
        if summary["count"]:
            return summary["next_level"]
        return 1


reminder_repository = ReminderRepository()
