from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _font_name():
    for path in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ):
        if path.exists():
            if "JuTanInvoice" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("JuTanInvoice", str(path)))
            return "JuTanInvoice"
    return "Helvetica"


def generate_invoice_pdf(path, invoice, customer, items, payments, company=None):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    font = _font_name()
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("InvoiceNormal", parent=styles["Normal"], fontName=font)
    title = ParagraphStyle(
        "InvoiceTitle", parent=styles["Title"], fontName=font,
        textColor=colors.HexColor("#0F766E"),
    )
    right = ParagraphStyle("InvoiceRight", parent=normal, alignment=TA_RIGHT)
    company = company or {"company_name": "JU-TAN Studio"}
    doc = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"Račun {invoice[1]}", author=company["company_name"],
    )
    story = [
        Paragraph(escape(company["company_name"]), title),
        Paragraph(f"RAČUN {escape(str(invoice[1]))}", right),
        Spacer(1, 6*mm),
    ]
    issuer = [
        company.get("address"),
        f'{company.get("postal_code", "")} {company.get("city", "")}'.strip(),
        company.get("tax_number") and f'Davčna št.: {company["tax_number"]}',
        company.get("registration_number") and f'Matična št.: {company["registration_number"]}',
        company.get("iban") and f'IBAN: {company["iban"]}',
        company.get("bank_name"), company.get("email"), company.get("phone"),
    ]
    story.extend([Paragraph("<br/>".join(escape(str(x)) for x in filter(None, issuer)), normal), Spacer(1, 4*mm)])
    address = [customer[1], customer[3], f"{customer[4]} {customer[5]}".strip()]
    if customer[7]:
        address.append(f"Davčna št.: {customer[7]}")
    info = Table([[
        Paragraph("Prejemnik<br/>" + "<br/>".join(escape(str(x)) for x in filter(None, address)), normal),
        Paragraph(
            f"Datum izdaje: {escape(str(invoice[4]))}<br/>"
            f"Zapadlost: {escape(str(invoice[5]))}<br/>"
            f"Status: {escape(str(invoice[6]))}", right,
        ),
    ]], colWidths=[95*mm, 75*mm])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([info, Spacer(1, 8*mm)])
    rows = [["Šifra", "Naziv", "Kol.", "Enota", "Cena", "Popust", "DDV", "Skupaj"]]
    for item in items:
        rows.append([
            item[2] or "", item[3] or "", f"{item[5]:.3f}", item[6] or "",
            f"{item[7]:.2f} €", f"{item[8]:.2f} %", f"{item[9]:.2f} %",
            f"{item[10]:.2f} €",
        ])
    table = Table(rows, repeatRows=1, colWidths=[18*mm,39*mm,16*mm,16*mm,21*mm,18*mm,16*mm,25*mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.extend([table, Spacer(1, 6*mm)])
    remaining = invoice[10] - invoice[11]
    totals = Table([
        ["Osnova:", f"{invoice[7]:.2f} €"], ["Popust:", f"-{invoice[8]:.2f} €"],
        ["DDV:", f"{invoice[9]:.2f} €"], ["SKUPAJ:", f"{invoice[10]:.2f} €"],
        ["Plačano:", f"{invoice[11]:.2f} €"], ["ZA PLAČILO:", f"{remaining:.2f} €"],
    ], colWidths=[40*mm, 35*mm], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#0F766E")),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
    ]))
    story.append(totals)
    if payments:
        story.extend([Spacer(1, 7*mm), Paragraph("Evidentirana plačila", normal)])
        pay_rows = [["Datum", "Način", "Referenca", "Znesek"]]
        pay_rows.extend([[p[1], p[3] or "", p[4] or "", f"{p[2]:.2f} €"] for p in payments])
        pay_table = Table(pay_rows, colWidths=[30*mm, 45*mm, 55*mm, 35*mm])
        pay_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(pay_table)
    if company.get("invoice_footer"):
        story.extend([Spacer(1, 8*mm), Paragraph(escape(company["invoice_footer"]), normal)])
    doc.build(story)
    return output
