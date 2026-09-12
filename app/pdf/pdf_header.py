from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from app.pdf.pdf_images import pdf_image
from app.pdf.pdf_styles import BORDER, PAD, SURFACE, styles


def build_header(company, options: dict):
    look = styles()
    logo = None
    if options.get("show_logo"):
        logo = pdf_image(company.logo, 42, 22)

    city_line = " ".join(
        part for part in (company.postal_code, company.city) if part
    ).strip()
    lines = [
        Paragraph(company.name or "JU-TAN Office", look["company"]),
        Paragraph(company.address or "", look["meta"]),
        Paragraph(city_line, look["meta"]),
        Paragraph(company.phone or company.mobile or "", look["meta"]),
        Paragraph(company.email or "", look["meta"]),
        Paragraph(f"Davčna: {company.tax_number}" if company.tax_number else "", look["meta"]),
    ]
    right = [line for line in lines if getattr(line, "text", True)]

    left = logo if logo is not None else Spacer(42 * mm, 8)
    table = Table(
        [[left, right]],
        colWidths=[55 * mm, 125 * mm],
    )
    table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), PAD / 2),
            ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
            ("LINEBELOW", (0, 0), (-1, -1), 0.6, BORDER),
        ])
    )
    return [table, Spacer(1, PAD)]
