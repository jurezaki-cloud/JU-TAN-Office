from datetime import date
from decimal import Decimal

from app.core.validation import money_for_storage, optional_text, required_text
from app.database.database import db


class InvoiceRepository:
    def __init__(self, database=None):
        self.db = database or db

    @staticmethod
    def _next_number(conn, year):
        row = conn.execute(
            """SELECT last_number FROM document_sequences
               WHERE document_type=? AND year=?""",
            ("invoice", year),
        ).fetchone()
        value = (row[0] if row else 0) + 1
        conn.execute(
            """INSERT INTO document_sequences(document_type, year, last_number)
               VALUES (?, ?, ?)
               ON CONFLICT(document_type, year)
               DO UPDATE SET last_number=excluded.last_number""",
            ("invoice", year, value),
        )
        return f"R-{year}-{value:06d}"

    def get_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT i.id, i.number, c.company, i.issue_date, i.due_date,
                          CASE
                            WHEN i.status <> 'Plačan' AND i.due_date < date('now')
                              THEN 'Zapadel'
                            ELSE i.status
                          END,
                          i.total, i.paid_amount
                   FROM invoices i JOIN customers c ON c.id=i.customer_id
                   ORDER BY i.id DESC"""
            ).fetchall()

    def get_by_id(self, invoice_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM invoices WHERE id=?", (invoice_id,)
            ).fetchone()

    def get_items(self, invoice_id):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, article_id, code, name, description, quantity,
                          unit, price, discount, vat, total
                   FROM invoice_items WHERE invoice_id=? ORDER BY id""",
                (invoice_id,),
            ).fetchall()

    def get_payments(self, invoice_id):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, payment_date, amount, method, reference, notes
                   FROM payments WHERE invoice_id=? ORDER BY payment_date, id""",
                (invoice_id,),
            ).fetchall()

    def get_all_payments(self):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT p.id, p.payment_date, i.number, c.company,
                          p.amount, p.method, p.reference
                   FROM payments p
                   JOIN invoices i ON i.id=p.invoice_id
                   JOIN customers c ON c.id=i.customer_id
                   ORDER BY p.payment_date DESC, p.id DESC"""
            ).fetchall()

    def create_from_offer(self, offer_id, issue_date, due_date):
        issue = date.fromisoformat(required_text(issue_date, "Datum izdaje", 10))
        due = date.fromisoformat(required_text(due_date, "Datum zapadlosti", 10))
        if due < issue:
            raise ValueError("Datum zapadlosti ne sme biti pred datumom izdaje.")

        with self.db.transaction(immediate=True) as conn:
            offer = conn.execute(
                "SELECT * FROM offers WHERE id=?", (offer_id,)
            ).fetchone()
            if offer is None:
                raise LookupError("Ponudba ne obstaja.")
            if offer[5] != "Sprejeta":
                raise ValueError("V račun je mogoče pretvoriti samo sprejeto ponudbo.")
            existing = conn.execute(
                "SELECT id FROM invoices WHERE source_offer_id=?", (offer_id,)
            ).fetchone()
            if existing:
                raise ValueError("Ta ponudba je že bila pretvorjena v račun.")
            items = conn.execute(
                """SELECT article_id, code, name, description, quantity, unit,
                          price, discount, vat, total
                   FROM offer_items WHERE offer_id=? ORDER BY id""",
                (offer_id,),
            ).fetchall()
            if not items:
                raise ValueError("Ponudba nima postavk.")

            number = self._next_number(conn, issue.year)
            cursor = conn.execute(
                """INSERT INTO invoices(
                       number, customer_id, source_offer_id, issue_date, due_date,
                       status, subtotal, discount, vat, total, paid_amount, notes
                   ) VALUES(?,?,?,?,?,'Neplačan',?,?,?,?,0,?)""",
                (
                    number, offer[2], offer_id, issue.isoformat(), due.isoformat(),
                    offer[6], offer[7], offer[8], offer[9], offer[10],
                ),
            )
            invoice_id = cursor.lastrowid
            conn.executemany(
                """INSERT INTO invoice_items(
                       invoice_id, article_id, code, name, description, quantity,
                       unit, price, discount, vat, total
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                [(invoice_id, *item) for item in items],
            )
            return invoice_id

    def add_payment(
        self, invoice_id, payment_date, amount, method="Bančno nakazilo",
        reference="", notes="",
    ):
        paid_on = date.fromisoformat(required_text(payment_date, "Datum plačila", 10))
        value = Decimal(str(money_for_storage(amount, "Znesek plačila")))
        if value <= 0:
            raise ValueError("Znesek plačila mora biti večji od 0.")
        with self.db.transaction(immediate=True) as conn:
            invoice = conn.execute(
                "SELECT total, paid_amount FROM invoices WHERE id=?", (invoice_id,)
            ).fetchone()
            if invoice is None:
                raise LookupError("Račun ne obstaja.")
            total = Decimal(str(invoice[0]))
            already_paid = Decimal(str(invoice[1]))
            if already_paid + value > total:
                raise ValueError("Plačilo ne sme biti večje od odprtega zneska.")
            conn.execute(
                """INSERT INTO payments(
                       invoice_id, payment_date, amount, method, reference, notes
                   ) VALUES(?,?,?,?,?,?)""",
                (
                    invoice_id, paid_on.isoformat(), float(value),
                    optional_text(method, "Način plačila", 50),
                    optional_text(reference, "Referenca", 100),
                    optional_text(notes, "Opombe", 1000),
                ),
            )
            new_paid = already_paid + value
            status = "Plačan" if new_paid == total else "Delno plačan"
            conn.execute(
                "UPDATE invoices SET paid_amount=?, status=? WHERE id=?",
                (float(new_paid), status, invoice_id),
            )


invoice_repository = InvoiceRepository()
