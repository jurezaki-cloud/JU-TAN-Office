from decimal import Decimal

from app.core.validation import (
    decimal_value,
    money_for_storage,
    optional_text,
    percentage_for_storage,
    required_text,
)
from app.database.database import db
from app.services.offer_calculation import calculate_offer


class OfferRepository:
    def __init__(self, database=None):
        self.db = database or db

    def get_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT o.id, o.number, c.company, o.issue_date,
                          o.valid_until, o.status, o.total
                   FROM offers o
                   JOIN customers c ON c.id=o.customer_id
                   ORDER BY o.id DESC"""
            ).fetchall()

    def get_by_id(self, offer_id):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM offers WHERE id=?", (offer_id,)
            ).fetchone()

    @staticmethod
    def _validated_offer(
        number, customer_id, issue_date, valid_until, status,
        subtotal, discount, vat, total, notes,
    ):
        if not isinstance(customer_id, int) or customer_id <= 0:
            raise ValueError("Izbrati morate veljavno stranko.")
        return (
            required_text(number, "Številka", 50),
            customer_id,
            required_text(issue_date, "Datum izdaje", 20),
            optional_text(valid_until, "Veljavnost", 20),
            required_text(status, "Status", 30),
            money_for_storage(subtotal, "Osnova"),
            money_for_storage(discount, "Popust"),
            money_for_storage(vat, "DDV"),
            money_for_storage(total, "Skupaj"),
            optional_text(notes, "Opombe", 4000),
        )

    def create(
        self, number, customer_id, issue_date, valid_until, status,
        subtotal, discount, vat, total, notes,
    ):
        values = self._validated_offer(
            number, customer_id, issue_date, valid_until, status,
            subtotal, discount, vat, total, notes,
        )
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO offers(
                       number, customer_id, issue_date, valid_until, status,
                       subtotal, discount, vat, total, notes
                   ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            return cursor.lastrowid

    def update(
        self, offer_id, customer_id, issue_date, valid_until, status,
        subtotal, discount, vat, total, notes,
    ):
        current = self.get_by_id(offer_id)
        if current is None:
            raise LookupError("Ponudba ne obstaja.")
        values = self._validated_offer(
            current[1], customer_id, issue_date, valid_until, status,
            subtotal, discount, vat, total, notes,
        )[1:]
        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE offers
                   SET customer_id=?, issue_date=?, valid_until=?, status=?,
                       subtotal=?, discount=?, vat=?, total=?, notes=?
                   WHERE id=?""",
                (*values, offer_id),
            )

    def delete(self, offer_id):
        with self.db.transaction() as conn:
            linked = conn.execute(
                "SELECT 1 FROM invoices WHERE source_offer_id=?", (offer_id,)
            ).fetchone()
            if linked:
                raise ValueError(
                    "Ponudbe ni mogoče izbrisati, ker je iz nje ustvarjen račun."
                )
            cursor = conn.execute("DELETE FROM offers WHERE id=?", (offer_id,))
            if cursor.rowcount == 0:
                raise LookupError("Ponudba ne obstaja.")

    def get_items(self, offer_id):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, article_id, code, name, description, quantity,
                          unit, price, discount, vat, total
                   FROM offer_items WHERE offer_id=? ORDER BY id""",
                (offer_id,),
            ).fetchall()

    def add_item(
        self, offer_id, article_id, code, name, description, quantity,
        unit, price, discount, vat, total,
    ):
        values = (
            offer_id,
            article_id,
            optional_text(code, "Šifra", 50),
            required_text(name, "Naziv"),
            optional_text(description, "Opis", 2000),
            float(
                decimal_value(
                    quantity, "Količina", quantum=Decimal("0.001")
                )
            ),
            required_text(unit, "Enota", 30),
            money_for_storage(price, "Cena"),
            percentage_for_storage(discount, "Popust"),
            percentage_for_storage(vat, "DDV"),
            money_for_storage(total, "Skupaj"),
        )
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO offer_items(
                       offer_id, article_id, code, name, description, quantity,
                       unit, price, discount, vat, total
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            return cursor.lastrowid

    def delete_items(self, offer_id):
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))

    @staticmethod
    def _insert_items(conn, offer_id, items):
        for item in items:
            conn.execute(
                """INSERT INTO offer_items(
                       offer_id, article_id, code, name, description, quantity,
                       unit, price, discount, vat, total
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    offer_id,
                    item.get("article_id"),
                    optional_text(item.get("code"), "Šifra", 50),
                    required_text(item.get("name"), "Naziv"),
                    optional_text(item.get("description"), "Opis", 2000),
                    float(decimal_value(
                        item.get("quantity"), "Količina",
                        quantum=Decimal("0.001"),
                    )),
                    required_text(item.get("unit"), "Enota", 30),
                    money_for_storage(item.get("price"), "Cena"),
                    percentage_for_storage(item.get("discount"), "Popust"),
                    percentage_for_storage(item.get("vat"), "DDV"),
                    money_for_storage(item.get("total"), "Skupaj"),
                ),
            )

    def create_with_items(
        self, number, customer_id, issue_date, valid_until, status, notes, items,
    ):
        calculation = calculate_offer(items)
        values = self._validated_offer(
            number, customer_id, issue_date, valid_until, status,
            calculation["subtotal"], calculation["discount"],
            calculation["vat"], calculation["total"], notes,
        )
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO offers(
                       number, customer_id, issue_date, valid_until, status,
                       subtotal, discount, vat, total, notes
                   ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            self._insert_items(conn, cursor.lastrowid, calculation["items"])
            return cursor.lastrowid

    def update_with_items(
        self, offer_id, customer_id, issue_date, valid_until, status, notes, items,
    ):
        current = self.get_by_id(offer_id)
        if current is None:
            raise LookupError("Ponudba ne obstaja.")
        calculation = calculate_offer(items)
        values = self._validated_offer(
            current[1], customer_id, issue_date, valid_until, status,
            calculation["subtotal"], calculation["discount"],
            calculation["vat"], calculation["total"], notes,
        )[1:]
        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE offers
                   SET customer_id=?, issue_date=?, valid_until=?, status=?,
                       subtotal=?, discount=?, vat=?, total=?, notes=?
                   WHERE id=?""",
                (*values, offer_id),
            )
            conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))
            self._insert_items(conn, offer_id, calculation["items"])


offer_repository = OfferRepository()
