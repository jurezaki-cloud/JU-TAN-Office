from app.database.database import db


class CompanyRepository:

    # =====================================================
    # Pridobi podatke podjetja
    # =====================================================

    def get_company(self):

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
                notes
            FROM company
            WHERE id = 1
        """)

        row = cursor.fetchone()

        conn.close()

        return row

    # =====================================================
    # Shrani podatke podjetja
    # =====================================================

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
    ):

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
                notes=?
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
        ))

        conn.commit()
        conn.close()


company_repository = CompanyRepository()