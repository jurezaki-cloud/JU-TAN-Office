from app.core.validation import normalize_email, optional_text, required_text
from app.database.database import db


class CustomerRepository:
    def __init__(self, database=None):
        self.db = database or db

    @staticmethod
    def _validated_data(
        company, contact, address, postal_code, city, country,
        tax_number, email, phone,
    ):
        return (
            required_text(company, "Podjetje"),
            optional_text(contact, "Kontakt", 200),
            optional_text(address, "Naslov", 300),
            optional_text(postal_code, "Poštna številka", 20),
            optional_text(city, "Kraj", 120),
            optional_text(country, "Država", 120),
            optional_text(tax_number, "Davčna številka", 30),
            normalize_email(email),
            optional_text(phone, "Telefon", 50),
        )

    def get_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, company, contact, phone, email, city
                   FROM customers ORDER BY company"""
            ).fetchall()

    def get_by_id(self, customer_id):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, company, contact, address, postal_code, city,
                          country, tax_number, email, phone
                   FROM customers WHERE id = ?""",
                (customer_id,),
            ).fetchone()

    def add(
        self, company, contact, address, postal_code, city, country,
        tax_number, email, phone,
    ):
        values = self._validated_data(
            company, contact, address, postal_code, city, country,
            tax_number, email, phone,
        )
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO customers(
                       company, contact, address, postal_code, city, country,
                       tax_number, email, phone
                   ) VALUES(?,?,?,?,?,?,?,?,?)""",
                values,
            )
            return cursor.lastrowid

    def update(
        self, customer_id, company, contact, address, postal_code, city,
        country, tax_number, email, phone,
    ):
        values = self._validated_data(
            company, contact, address, postal_code, city, country,
            tax_number, email, phone,
        )
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """UPDATE customers
                   SET company=?, contact=?, address=?, postal_code=?, city=?,
                       country=?, tax_number=?, email=?, phone=?
                   WHERE id=?""",
                (*values, customer_id),
            )
            if cursor.rowcount == 0:
                raise LookupError("Stranka ne obstaja.")

    def delete(self, customer_id):
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM customers WHERE id=?", (customer_id,)
            )
            if cursor.rowcount == 0:
                raise LookupError("Stranka ne obstaja.")

    def search(self, text):
        pattern = f"%{optional_text(text, 'Iskanje', 200)}%"
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT id, company, contact, phone, email, city
                   FROM customers
                   WHERE company LIKE ? OR contact LIKE ? OR city LIKE ?
                   ORDER BY company""",
                (pattern, pattern, pattern),
            ).fetchall()


customer_repository = CustomerRepository()
