from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database.company_repository import company_repository
from app.modules.settings.settings_controller import SettingsController


@dataclass
class CompanyProfile:
    name: str = ""
    address: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = ""
    phone: str = ""
    mobile: str = ""
    email: str = ""
    tax_number: str = ""
    iban: str = ""
    swift: str = ""
    logo: str = ""
    website: str = ""


def load_company() -> CompanyProfile:
    extras = SettingsController().load_extras()
    row = company_repository.get_company()
    if not row:
        return CompanyProfile(swift=extras.get("swift", ""))
    return CompanyProfile(
        name=row[1] or row[2] or "",
        address=row[3] or "",
        postal_code=row[4] or "",
        city=row[5] or "",
        country=row[6] or "",
        tax_number=row[7] or "",
        iban=row[9] or "",
        email=row[11] or "",
        website=row[12] or "",
        phone=row[13] or "",
        mobile=row[14] or "",
        logo=row[15] or "",
        swift=extras.get("swift", ""),
    )


def load_pdf_options() -> dict:
    from app.utils.vat import DOCUMENT_FOOTER_MESSAGE, WEBSITE_URL

    pdf = SettingsController().load_extras().get("pdf", {})
    footer = str(pdf.get("footer") or DOCUMENT_FOOTER_MESSAGE).strip()
    # Migrate legacy marketing footer to the professional default.
    if "JU-TAN Office Enterprise" in footer or footer == "Hvala za zaupanje.":
        footer = DOCUMENT_FOOTER_MESSAGE
    return {
        "show_logo": bool(pdf.get("logo", True)),
        "show_signature": bool(pdf.get("signature", True)),
        "show_stamp": bool(pdf.get("stamp", True)),
        "show_vat": bool(pdf.get("vat", True)),
        "show_discount": bool(pdf.get("discounts", True)),
        "show_notes": bool(pdf.get("notes", True)),
        "folder": str(pdf.get("folder") or ""),
        "footer": footer or DOCUMENT_FOOTER_MESSAGE,
        "signature_path": str(pdf.get("signature_path") or ""),
        "stamp_path": str(pdf.get("stamp_path") or ""),
        "payment_method": str(pdf.get("payment_method") or "Nakazilo"),
        "website_url": WEBSITE_URL,
    }


def existing_path(*candidates: str) -> str:
    for raw in candidates:
        if raw and Path(raw).exists():
            return raw
    return ""
