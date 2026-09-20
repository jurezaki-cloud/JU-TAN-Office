from app.database.database import db
from app.utils.vat import parse_vat_liable, vat_liable_int


class CompanyRepository:

    def ensure_schema(self) -> None:
        """Add vat_liable to company without destroying existing rows."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
        )
        if cursor.fetchone():
            cols = {
                row[1]
                for row in cursor.execute("PRAGMA table_info(company)").fetchall()
            }
            if "vat_liable" not in cols:
                cursor.execute(
                    "ALTER TABLE company ADD COLUMN vat_liable INTEGER DEFAULT 1"
                )
                cursor.execute(
                    "UPDATE company SET vat_liable=1 WHERE vat_liable IS NULL"
                )
        conn.commit()
        conn.close()

    def get_company(self):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                legal_name,
                address,
                postal_code,
                city,
                country,
                tax_number,
                registration_number,
                iban,
                bank,
                email,
                website,
                phone,
                mobile,
                logo,
                invoice_prefix,
                offer_prefix,
                invoice_counter,
                offer_counter,
                default_vat,
                notes,
                vat_liable
            FROM company
            WHERE id = 1
        """)

        row = cursor.fetchone()
        conn.close()
        return row

    # Alias used by CompanyService.load()
    get = get_company

    def is_vat_liable(self) -> bool:
        row = self.get_company()
        if not row or len(row) < 23:
            return True
        return parse_vat_liable(row[22])

    def set_vat_liable(self, vat_liable) -> None:
        """Persist only the VAT-registration flag (source of truth for new documents)."""
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE company SET vat_liable=? WHERE id = 1",
            (vat_liable_int(vat_liable),),
        )
        conn.commit()
        conn.close()

    def save(
        self,
        name,
        legal_name,
        address,
        postal_code,
        city,
        country,
        tax_number,
        registration_number,
        iban,
        bank,
        email,
        website,
        phone,
        mobile,
        logo,
        invoice_prefix,
        offer_prefix,
        invoice_counter,
        offer_counter,
        default_vat,
        notes,
        vat_liable=1,
    ):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE company
            SET
                name=?,
                legal_name=?,
                address=?,
                postal_code=?,
                city=?,
                country=?,
                tax_number=?,
                registration_number=?,
                iban=?,
                bank=?,
                email=?,
                website=?,
                phone=?,
                mobile=?,
                logo=?,
                invoice_prefix=?,
                offer_prefix=?,
                invoice_counter=?,
                offer_counter=?,
                default_vat=?,
                notes=?,
                vat_liable=?
            WHERE id = 1
        """, (
            name,
            legal_name,
            address,
            postal_code,
            city,
            country,
            tax_number,
            registration_number,
            iban,
            bank,
            email,
            website,
            phone,
            mobile,
            logo,
            invoice_prefix,
            offer_prefix,
            invoice_counter,
            offer_counter,
            default_vat,
            notes,
            vat_liable_int(vat_liable),
        ))

        conn.commit()
        conn.close()


company_repository = CompanyRepository()
