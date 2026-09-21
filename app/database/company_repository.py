from app.database.database import db
from app.database.migrations import (
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    DEFAULT_TABLE_HEADER,
    migrate_company_branding,
)
from app.utils.vat import parse_vat_liable, vat_liable_int


class CompanyRepository:

    def ensure_schema(self) -> None:
        """Ensure vat_liable + branding columns (idempotent safety net for v3)."""
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
            migrate_company_branding(conn)
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
                vat_liable,
                signature_path,
                stamp_path,
                doc_primary_color,
                doc_accent_color,
                doc_table_header_color
            FROM company
            WHERE id = 1
        """)

        row = cursor.fetchone()
        conn.close()
        return row

    # Alias used by CompanyService.load()
    get = get_company

    def get_branding(self) -> dict:
        """Return document branding paths and colors (DB is source of truth)."""
        row = self.get_company()
        if not row:
            return {
                "logo": "",
                "signature_path": "",
                "stamp_path": "",
                "doc_primary_color": DEFAULT_PRIMARY,
                "doc_accent_color": DEFAULT_ACCENT,
                "doc_table_header_color": DEFAULT_TABLE_HEADER,
            }
        return {
            "logo": (row[15] or "") if len(row) > 15 else "",
            "signature_path": (row[23] or "") if len(row) > 23 else "",
            "stamp_path": (row[24] or "") if len(row) > 24 else "",
            "doc_primary_color": (row[25] or DEFAULT_PRIMARY) if len(row) > 25 else DEFAULT_PRIMARY,
            "doc_accent_color": (row[26] or DEFAULT_ACCENT) if len(row) > 26 else DEFAULT_ACCENT,
            "doc_table_header_color": (
                (row[27] or DEFAULT_TABLE_HEADER) if len(row) > 27 else DEFAULT_TABLE_HEADER
            ),
        }

    def save_branding(
        self,
        *,
        logo: str | None = None,
        signature_path: str | None = None,
        stamp_path: str | None = None,
        doc_primary_color: str | None = None,
        doc_accent_color: str | None = None,
        doc_table_header_color: str | None = None,
    ) -> None:
        """Update branding fields only; None means leave unchanged."""
        self.ensure_schema()
        current = self.get_branding()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE company SET
                logo=?,
                signature_path=?,
                stamp_path=?,
                doc_primary_color=?,
                doc_accent_color=?,
                doc_table_header_color=?
            WHERE id = 1
            """,
            (
                current["logo"] if logo is None else (logo or ""),
                current["signature_path"] if signature_path is None else (signature_path or ""),
                current["stamp_path"] if stamp_path is None else (stamp_path or ""),
                current["doc_primary_color"]
                if doc_primary_color is None
                else (doc_primary_color or DEFAULT_PRIMARY),
                current["doc_accent_color"]
                if doc_accent_color is None
                else (doc_accent_color or DEFAULT_ACCENT),
                current["doc_table_header_color"]
                if doc_table_header_color is None
                else (doc_table_header_color or DEFAULT_TABLE_HEADER),
            ),
        )
        conn.commit()
        conn.close()

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
