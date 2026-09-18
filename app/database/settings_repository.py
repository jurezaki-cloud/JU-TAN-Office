from app.core.validation import normalize_email, optional_text, required_text
from app.database.database import db


FIELDS = (
    "company_name", "address", "postal_code", "city", "country",
    "tax_number", "registration_number", "iban", "bank_name", "email",
    "phone", "website", "invoice_footer", "payment_terms_days",
    "auto_backup", "backup_retention_days",
)


class SettingsRepository:
    def __init__(self, database=None):
        self.db = database or db

    def get(self):
        with self.db.connect() as conn:
            row = conn.execute(
                f"SELECT {', '.join(FIELDS)} FROM company_settings WHERE id=1"
            ).fetchone()
        return dict(zip(FIELDS, row))

    def update(self, values):
        payment_days = int(values.get("payment_terms_days", 15))
        retention_days = int(values.get("backup_retention_days", 30))
        if not 1 <= payment_days <= 365:
            raise ValueError("Rok plačila mora biti med 1 in 365 dnevi.")
        if not 1 <= retention_days <= 3650:
            raise ValueError("Hramba kopij mora biti med 1 in 3650 dnevi.")
        normalized = (
            required_text(values.get("company_name"), "Naziv podjetja"),
            optional_text(values.get("address"), "Naslov", 300),
            optional_text(values.get("postal_code"), "Poštna številka", 20),
            optional_text(values.get("city"), "Kraj", 120),
            required_text(values.get("country") or "Slovenija", "Država", 120),
            optional_text(values.get("tax_number"), "Davčna številka", 30),
            optional_text(values.get("registration_number"), "Matična številka", 30),
            optional_text(values.get("iban"), "IBAN", 50).replace(" ", "").upper(),
            optional_text(values.get("bank_name"), "Banka", 150),
            normalize_email(values.get("email")),
            optional_text(values.get("phone"), "Telefon", 50),
            optional_text(values.get("website"), "Spletna stran", 200),
            optional_text(values.get("invoice_footer"), "Noga dokumenta", 1000),
            payment_days,
            1 if values.get("auto_backup", True) else 0,
            retention_days,
        )
        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE company_settings SET
                       company_name=?, address=?, postal_code=?, city=?, country=?,
                       tax_number=?, registration_number=?, iban=?, bank_name=?,
                       email=?, phone=?, website=?, invoice_footer=?,
                       payment_terms_days=?, auto_backup=?, backup_retention_days=?,
                       updated_at=CURRENT_TIMESTAMP
                   WHERE id=1""",
                normalized,
            )
        return self.get()


settings_repository = SettingsRepository()
