"""Payment ledger repository (partial/full payments)."""

from __future__ import annotations

from app.database.database import db
from app.utils.money import as_float, money, to_decimal


class PaymentRepository:

    def ensure_schema(self) -> None:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                paid_date TEXT NOT NULL,
                amount REAL NOT NULL,
                method TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)"
        )
        conn.commit()
        conn.close()

    def add(self, invoice_id, paid_date, amount, method, notes="") -> int:
        self.ensure_schema()
        from app.database.invoice_repository import invoice_repository

        invoice = invoice_repository.get_by_id(invoice_id)
        if invoice is None:
            raise ValueError("Račun ne obstaja.")
        if (invoice[5] or "").strip() == "Storniran":
            raise ValueError("Storniranega računa ni mogoče plačati.")

        value = money(amount)
        if value <= 0:
            raise ValueError("Znesek plačila mora biti večji od 0.")
        remaining = money(self.remaining(invoice_id, invoice[9] or 0))
        if value > remaining:
            raise ValueError("Znesek plačila presega preostalo vsoto.")

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments(invoice_id, paid_date, amount, method, notes)
            VALUES (?,?,?,?,?)
            """,
            (invoice_id, paid_date, as_float(value), method, notes),
        )
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        return payment_id

    def sum_for_invoice(self, invoice_id) -> float:
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
            (invoice_id,),
        )
        total = cursor.fetchone()[0]
        conn.close()
        return float(total or 0)

    def list_for_invoice(self, invoice_id):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, paid_date, amount, method, notes
            FROM payments
            WHERE invoice_id=?
            ORDER BY paid_date, id
            """,
            (invoice_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def remaining(self, invoice_id, invoice_total) -> float:
        paid = to_decimal(self.sum_for_invoice(invoice_id))
        total = to_decimal(invoice_total)
        rem = total - paid
        if rem < 0:
            rem = money(0)
        return as_float(rem)

    def sync_invoice_status(self, invoice_id, invoice_total) -> str:
        """Update invoice status from payment ledger. Returns new status."""
        from app.database.invoice_repository import invoice_repository

        current = invoice_repository.get_by_id(invoice_id)
        if current is None:
            return ""
        if (current[5] or "").strip() == "Storniran":
            return "Storniran"

        paid = money(self.sum_for_invoice(invoice_id))
        total = money(invoice_total)
        if paid <= 0:
            status = "Izdan"
        elif paid + money("0.01") >= total:
            status = "Plačan"
        else:
            status = "Delno plačan"

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE invoices SET status=? WHERE id=?",
            (status, invoice_id),
        )
        conn.commit()
        conn.close()
        # keep repository helper available for callers that only mark paid
        _ = invoice_repository
        return status


payment_repository = PaymentRepository()
