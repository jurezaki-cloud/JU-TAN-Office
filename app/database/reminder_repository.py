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

    def attention_summary(self, today: date | None = None) -> dict:
        """Return collection KPIs for the Payment Center without changing data."""
        self.ensure_schema()
        today = today or date.today()
        conn = db.connect()
        rows = conn.execute("""
            SELECT i.id, i.total, COALESCE(p.paid, 0),
                   COALESCE(r.level, 0), COALESCE(r.sent_at, '')
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS paid
                FROM payments GROUP BY invoice_id
            ) p ON p.invoice_id=i.id
            LEFT JOIN (
                SELECT pr.invoice_id, pr.level, pr.sent_at
                FROM payment_reminders pr
                JOIN (
                    SELECT invoice_id, MAX(id) AS max_id
                    FROM payment_reminders GROUP BY invoice_id
                ) latest ON latest.max_id=pr.id
            ) r ON r.invoice_id=i.id
            WHERE i.status NOT IN ('Osnutek', 'Storniran', 'Plačan')
              AND IFNULL(i.due_date, '') != '' AND i.due_date < ?
              AND (i.total - COALESCE(p.paid, 0)) > 0.009
        """, (today.isoformat(),)).fetchall()
        conn.close()
        result = {"overdue_count": len(rows), "overdue_amount": 0.0,
                  "without_reminder": 0, "first": 0, "second": 0, "third": 0}
        for row in rows:
            result["overdue_amount"] += max(0.0, float(row[1] or 0) - float(row[2] or 0))
            level = int(row[3] or 0)
            if level == 0:
                result["without_reminder"] += 1
            elif level == 1:
                result["first"] += 1
            elif level == 2:
                result["second"] += 1
            else:
                result["third"] += 1
        return result


reminder_repository = ReminderRepository()
