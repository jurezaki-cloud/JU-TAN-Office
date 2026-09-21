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
        columns = {
            row[1] for row in cursor.execute("PRAGMA table_info(payments)").fetchall()
        }
        # Phase-8 databases keep legacy payment_date as NOT NULL. Keep both
        # date columns synchronized during the compatibility period.
        if "payment_date" in columns:
            cursor.execute(
                """
                INSERT INTO payments(
                    invoice_id, payment_date, paid_date, amount, method, notes
                )
                VALUES (?,?,?,?,?,?)
                """,
                (invoice_id, paid_date, paid_date, as_float(value), method, notes),
            )
        else:
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

    def sums_by_invoice_ids(self, invoice_ids) -> dict:
        """Return ``{invoice_id: paid_sum}`` in one GROUP BY query (dashboard N+1 fix).

        Invoices with no payment rows map to ``0.0``. Empty input yields ``{}``.
        """
        self.ensure_schema()
        ids = []
        seen = set()
        for raw in invoice_ids or ():
            if raw is None:
                continue
            try:
                invoice_id = int(raw)
            except (TypeError, ValueError):
                continue
            if invoice_id in seen:
                continue
            seen.add(invoice_id)
            ids.append(invoice_id)
        if not ids:
            return {}

        placeholders = ",".join("?" * len(ids))
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT invoice_id, COALESCE(SUM(amount), 0)
            FROM payments
            WHERE invoice_id IN ({placeholders})
            GROUP BY invoice_id
            """,
            ids,
        )
        paid = {row[0]: float(row[1] or 0) for row in cursor.fetchall()}
        conn.close()
        return {invoice_id: paid.get(invoice_id, 0.0) for invoice_id in ids}

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

    def remaining_map(self, totals_by_id) -> dict:
        """Batch ``remaining()`` for many invoices using one payment SUM query.

        *totals_by_id* maps ``invoice_id -> invoice_total``. Money math matches
        :meth:`remaining` exactly (no accounting-rule changes).
        """
        if not totals_by_id:
            return {}
        paid_by_id = self.sums_by_invoice_ids(list(totals_by_id.keys()))
        result = {}
        for invoice_id, invoice_total in totals_by_id.items():
            paid = to_decimal(paid_by_id.get(invoice_id, 0))
            rem = to_decimal(invoice_total) - paid
            if rem < 0:
                rem = money(0)
            result[invoice_id] = as_float(rem)
        return result

    def sync_invoice_status(self, invoice_id, invoice_total) -> str:
        """Update invoice status from payment ledger. Returns new status."""
        from app.core.ui_freeze_diag import span as _diag_span
        from app.database.invoice_repository import invoice_repository

        with _diag_span("PaymentRepository.sync_invoice_status", invoice_id=invoice_id):
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
