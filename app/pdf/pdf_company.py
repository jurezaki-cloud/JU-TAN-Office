from __future__ import annotations



from dataclasses import dataclass

from pathlib import Path



from app.database.company_repository import (

    DEFAULT_ACCENT,

    DEFAULT_PRIMARY,

    DEFAULT_TABLE_HEADER,

    company_repository,

)

from app.modules.settings.settings_controller import SettingsController

from app.pdf.pdf_branding import normalize_hex

from app.pdf.pdf_images import heal_logo_path

from app.utils.flags import parse_bool





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

    registration_number: str = ""

    iban: str = ""

    bank: str = ""

    swift: str = ""

    logo: str = ""

    website: str = ""

    signature_path: str = ""

    stamp_path: str = ""

    doc_primary_color: str = DEFAULT_PRIMARY

    doc_accent_color: str = DEFAULT_ACCENT

    doc_table_header_color: str = DEFAULT_TABLE_HEADER





def load_company() -> CompanyProfile:

    extras = SettingsController().load_extras()

    pdf = extras.get("pdf") or {}

    row = company_repository.get_company()

    branding = company_repository.get_branding()

    # Backward compatible: settings.json paths fill gaps when DB is empty.

    signature = branding.get("signature_path") or str(pdf.get("signature_path") or "")

    stamp = branding.get("stamp_path") or str(pdf.get("stamp_path") or "")

    if not row:

        return CompanyProfile(

            swift=extras.get("swift", ""),

            signature_path=signature,

            stamp_path=stamp,

            doc_primary_color=normalize_hex(

                branding.get("doc_primary_color"), DEFAULT_PRIMARY

            ),

            doc_accent_color=normalize_hex(

                branding.get("doc_accent_color"), DEFAULT_ACCENT

            ),

            doc_table_header_color=normalize_hex(

                branding.get("doc_table_header_color"), DEFAULT_TABLE_HEADER

            ),

        )

    raw_logo = row[15] or branding.get("logo") or ""

    return CompanyProfile(

        name=row[1] or row[2] or "",

        address=row[3] or "",

        postal_code=row[4] or "",

        city=row[5] or "",

        country=row[6] or "",

        tax_number=row[7] or "",

        registration_number=(row[8] or "").strip(),

        iban=row[9] or "",

        bank=row[10] or "",

        email=row[11] or "",

        website=row[12] or "",

        phone=row[13] or "",

        mobile=row[14] or "",

        logo=heal_logo_path(raw_logo),

        swift=extras.get("swift", ""),

        signature_path=signature,

        stamp_path=stamp,

        doc_primary_color=normalize_hex(

            branding.get("doc_primary_color"), DEFAULT_PRIMARY

        ),

        doc_accent_color=normalize_hex(

            branding.get("doc_accent_color"), DEFAULT_ACCENT

        ),

        doc_table_header_color=normalize_hex(

            branding.get("doc_table_header_color"), DEFAULT_TABLE_HEADER

        ),

    )





def load_pdf_options() -> dict:

    from app.utils.vat import DOCUMENT_FOOTER_MESSAGE, WEBSITE_URL



    company = load_company()

    pdf = SettingsController().load_extras().get("pdf", {})

    footer = str(pdf.get("footer") or DOCUMENT_FOOTER_MESSAGE).strip()

    # Migrate legacy marketing footer to the professional default.

    if "JU-TAN Office Enterprise" in footer or footer == "Hvala za zaupanje.":

        footer = DOCUMENT_FOOTER_MESSAGE

    # `logo` in settings.json is the visibility toggle only.

    # The image path lives in company branding (shared by all PDF documents).

    return {

        "show_logo": parse_bool(pdf.get("logo", True), default=True),

        "show_signature": parse_bool(pdf.get("signature", True), default=True),

        "show_stamp": parse_bool(pdf.get("stamp", True), default=True),

        "show_vat": parse_bool(pdf.get("vat", True), default=True),

        "show_discount": parse_bool(pdf.get("discounts", True), default=True),

        "show_notes": parse_bool(pdf.get("notes", True), default=True),

        "folder": str(pdf.get("folder") or ""),

        "footer": footer or DOCUMENT_FOOTER_MESSAGE,

        # DB branding wins; settings.json remains a fallback for older installs.

        "signature_path": company.signature_path or str(pdf.get("signature_path") or ""),

        "stamp_path": company.stamp_path or str(pdf.get("stamp_path") or ""),

        "payment_method": str(pdf.get("payment_method") or "Nakazilo"),

        "website_url": WEBSITE_URL,

        "colors": {

            "primary": company.doc_primary_color,

            "accent": company.doc_accent_color,

            "table_header": company.doc_table_header_color,

        },

    }





def existing_path(*candidates: str) -> str:

    for raw in candidates:

        if raw and Path(raw).exists():

            return raw

    return ""

