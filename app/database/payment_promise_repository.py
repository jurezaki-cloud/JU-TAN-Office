"""Customer payment promises, separate from confirmed payments."""
from __future__ import annotations

from datetime import date

from app.core.permissions import require
from app.database.database import db


class PaymentPromiseRepository:
    def ensure_schema(self):
        conn = db.connect()
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS payment_promises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                promised_date TEXT NOT NULL,
                expected_amount REAL NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_payment_promises_invoice ON payment_promises(invoice_id)")
            conn.commit()
        finally:
            conn.close()

    def record(self, invoice_id: int, promised_date: str, amount: float, note: str = "") -> int:
        require("write")
        date.fromisoformat(promised_date)
        if amount <= 0:
            raise ValueError("Pričakovani znesek mora biti večji od nič.")
        self.ensure_schema()
        conn = db.connect()
        try:
            invoice = conn.execute("SELECT total, status FROM invoices WHERE id=?",
                                   (invoice_id,)).fetchone()
            if not invoice or invoice[1] in ("Osnutek", "Storniran", "Plačan"):
                raise ValueError("Izberi odprt izdan račun.")
            paid = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id=?",
                                (invoice_id,)).fetchone()[0]
            if amount > max(0.0, float(invoice[0] or 0) - float(paid or 0)) + .001:
                raise ValueError("Obljubljeni znesek presega odprto terjatev.")
            cur = conn.execute("""INSERT INTO payment_promises
                (invoice_id, promised_date, expected_amount, note) VALUES (?, ?, ?, ?)""",
                (invoice_id, promised_date, amount, note.strip()))
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def latest(self, invoice_id: int):
        self.ensure_schema()
        conn = db.connect()
        try:
            return conn.execute("""SELECT promised_date, expected_amount, note
                FROM payment_promises WHERE invoice_id=? ORDER BY id DESC LIMIT 1""",
                (invoice_id,)).fetchone()
        finally:
            conn.close()

    def expected(self, today: date | None = None) -> tuple[float, float]:
        """Projection from latest promises only, capped at current invoice balance."""
        self.ensure_schema()
        start = (today or date.today()).isoformat()
        from datetime import timedelta
        end7 = ((today or date.today()) + timedelta(days=7)).isoformat()
        end30 = ((today or date.today()) + timedelta(days=30)).isoformat()
        conn = db.connect()
        try:
            rows = conn.execute("""
                SELECT p.promised_date, MIN(p.expected_amount,
                    MAX(0, i.total - COALESCE(pay.paid, 0)))
                FROM payment_promises p
                JOIN (SELECT invoice_id, MAX(id) AS last_id FROM payment_promises
                      GROUP BY invoice_id) latest ON latest.last_id=p.id
                JOIN invoices i ON i.id=p.invoice_id
                LEFT JOIN (SELECT invoice_id, SUM(amount) paid FROM payments
                           GROUP BY invoice_id) pay ON pay.invoice_id=i.id
                WHERE i.status NOT IN ('Osnutek', 'Storniran', 'Plačan')
                  AND p.promised_date BETWEEN ? AND ?
            """, (start, end30)).fetchall()
        finally:
            conn.close()
        return (sum(float(amount or 0) for day, amount in rows if day <= end7),
                sum(float(amount or 0) for _, amount in rows))


payment_promise_repository = PaymentPromiseRepository()
