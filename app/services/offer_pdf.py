from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


def _font_name():
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    )
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("JuTanUnicode", str(path)))
            return "JuTanUnicode"
    return "Helvetica"


def generate_offer_pdf(path, offer, customer, items, company=None):
    """Generate a clean A4 offer PDF and return its path."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    font = _font_name()
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("JuTanNormal", parent=styles["Normal"], fontName=font)
    heading = ParagraphStyle(
        "JuTanHeading", parent=styles["Title"], fontName=font,
        textColor=colors.HexColor("#0F766E"),
    )
    right = ParagraphStyle("JuTanRight", parent=normal, alignment=TA_RIGHT)
    company = company or {"company_name": "JU-TAN Studio"}
    document = SimpleDocTemplate(
        str(output), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Ponudba {offer[1]}", author=company["company_name"],
    )
    story = [
        Paragraph(escape(company["company_name"]), heading),
        Paragraph(f"PONUDBA {escape(str(offer[1]))}", right),
        Spacer(1, 6 * mm),
    ]
    issuer = [
        company.get("address"),
        f'{company.get("postal_code", "")} {company.get("city", "")}'.strip(),
        company.get("tax_number") and f'Davčna št.: {company["tax_number"]}',
        company.get("iban") and f'IBAN: {company["iban"]}',
        company.get("email"), company.get("phone"),
    ]
    story.extend([Paragraph("<br/>".join(escape(str(x)) for x in filter(None, issuer)), normal), Spacer(1, 4*mm)])
    customer_lines = [customer[1], customer[3], f"{customer[4]} {customer[5]}".strip()]
    if customer[7]:
        customer_lines.append(f"Davčna št.: {customer[7]}")
    info = Table([
        [Paragraph("Prejemnik<br/>" + "<br/>".join(escape(str(x)) for x in filter(None, customer_lines)), normal),
         Paragraph(
             f"Datum izdaje: {escape(str(offer[3]))}<br/>"
             f"Velja do: {escape(str(offer[4] or '-'))}<br/>"
             f"Status: {escape(str(offer[5]))}", right
         )],
    ], colWidths=[95 * mm, 75 * mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([info, Spacer(1, 8 * mm)])

    rows = [["Šifra", "Naziv", "Kol.", "Enota", "Cena", "Popust", "DDV", "Skupaj"]]
    for item in items:
        rows.append([
            item[2] or "", item[3] or "", f"{item[5]:.3f}", item[6] or "",
            f"{item[7]:.2f} €", f"{item[8]:.2f} %", f"{item[9]:.2f} %",
            f"{item[10]:.2f} €",
        ])
    table = Table(
        rows,
        repeatRows=1,
        colWidths=[18*mm, 39*mm, 16*mm, 16*mm, 21*mm, 18*mm, 16*mm, 25*mm],
    )
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([table, Spacer(1, 6 * mm)])
    totals = Table([
        ["Osnova:", f"{offer[6]:.2f} €"],
        ["Popust:", f"-{offer[7]:.2f} €"],
        ["DDV:", f"{offer[8]:.2f} €"],
        ["SKUPAJ:", f"{offer[9]:.2f} €"],
    ], colWidths=[40 * mm, 35 * mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#0F766E")),
        ("FONTNAME", (0, -1), (-1, -1), font),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
    ]))
    story.append(totals)
    if offer[10]:
        story.extend([
            Spacer(1, 8 * mm), Paragraph("Opombe", normal),
            Paragraph(escape(str(offer[10])), normal),
        ])
    if company.get("invoice_footer"):
        story.extend([Spacer(1, 8*mm), Paragraph(escape(company["invoice_footer"]), normal)])
    document.build(story)
    return output
