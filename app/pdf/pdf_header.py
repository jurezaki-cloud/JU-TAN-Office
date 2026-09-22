from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from app.pdf.pdf_branding import resolve_palette
from app.pdf.pdf_images import pdf_image
from app.pdf.pdf_styles import PAD, styles


def build_header(company, options: dict):
    """Modern ERP header: accent bar, logo, full company information block."""
    look = styles(options)
    palette = resolve_palette(options)

    accent_bar = Table([[""]], colWidths=[180 * mm], rowHeights=[3.2])
    accent_bar.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), palette["primary"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    logo = None
    if options.get("show_logo", True):
        # Prefer the selected company logo, then always fall back to the bundled
        # full horizontal JU-TAN mark. This path is shared by every PDF type.
        logo = pdf_image(company.logo, 48, 22)
        if logo is None:
            logo = pdf_image("resources/logo.png", 48, 22)

    city_line = " ".join(
        part for part in (company.postal_code, company.city) if part
    ).strip()
    if company.country:
        city_line = f"{city_line}, {company.country}".strip(", ")

    info_lines = [Paragraph(company.name or "JU-TAN Office", look["company"])]
    if company.address:
        info_lines.append(Paragraph(company.address, look["meta"]))
    if city_line:
        info_lines.append(Paragraph(city_line, look["meta"]))

    contact_bits = []
    if company.phone or company.mobile:
        contact_bits.append(company.phone or company.mobile)
    if company.email:
        contact_bits.append(company.email)
    if contact_bits:
        info_lines.append(Paragraph(" · ".join(contact_bits), look["meta"]))

    tax_bits = []
    if company.tax_number:
        tax_bits.append(f"Davčna: {company.tax_number}")
    if getattr(company, "registration_number", ""):
        tax_bits.append(f"Matična: {company.registration_number}")
    if tax_bits:
        info_lines.append(Paragraph(" · ".join(tax_bits), look["meta"]))

    if company.iban:
        bank = getattr(company, "bank", "") or ""
        iban_line = f"TRR: {company.iban}"
        if bank:
            iban_line = f"{iban_line} ({bank})"
        info_lines.append(Paragraph(iban_line, look["meta"]))

    left = logo if logo is not None else Spacer(48 * mm, 10)
    body = Table(
        [[left, info_lines]],
        colWidths=[52 * mm, 128 * mm],
    )
    body.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 2),
            ("RIGHTPADDING", (0, 0), (0, 0), 8),
            ("LEFTPADDING", (1, 0), (1, 0), 6),
            ("RIGHTPADDING", (1, 0), (1, 0), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, -1), palette["surface"]),
            ("BOX", (0, 0), (-1, -1), 0.4, palette["border"]),
            ("LINEBELOW", (0, 0), (-1, -1), 1.2, palette["primary"]),
        ])
    )
    return [accent_bar, Spacer(1, 4), body, Spacer(1, PAD)]
