from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.document_pdf import (
    LINE, PALE, footer_canvas, font_name, header, items_table, parties,
    payment_block, signature_block, styles, totals_table,
)


def generate_invoice_pdf(path, invoice, customer, items, payments, company=None):
    """Generate a branded invoice with a scannable SEPA payment QR code."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    company = company or {"company_name": "JU-TAN Studio"}
    font = font_name()
    style = styles(font)
    remaining = max(0, invoice[10] - invoice[11])
    doc = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
        topMargin=13*mm, bottomMargin=17*mm,
        title=f"Račun {invoice[1]}", author=company.get("company_name") or "JU-TAN Studio",
    )
    story = [
        header(company, "Račun", invoice[1], invoice[6], font, style), Spacer(1, 7*mm),
        parties(company, customer, [("Datum izdaje", invoice[4]), ("Zapadlost", invoice[5])], style),
        Spacer(1, 8*mm), items_table(items, font), Spacer(1, 6*mm),
        totals_table([
            ["Osnova", f"{invoice[7]:.2f} €"], ["Popust", f"-{invoice[8]:.2f} €"],
            ["DDV", f"{invoice[9]:.2f} €"], ["Skupaj", f"{invoice[10]:.2f} €"],
            ["Plačano", f"{invoice[11]:.2f} €"], ["ZA PLAČILO", f"{remaining:.2f} €"],
        ], font),
    ]
    payment = payment_block(company, remaining, invoice[1], font, style)
    if payment:
        story.extend([Spacer(1, 7*mm), payment])
    if payments:
        story.extend([Spacer(1, 7*mm), Paragraph("EVIDENTIRANA PLAČILA", style["section"])])
        rows = [["Datum", "Način", "Referenca", "Znesek"]]
        rows.extend([[p[1], p[3] or "", p[4] or "", f"{p[2]:.2f} €"] for p in payments])
        table = Table(rows, colWidths=[30*mm, 45*mm, 55*mm, 40*mm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), PALE), ("LINEBELOW", (0, 0), (-1, -1), .4, LINE),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
    if invoice[12]:
        story.extend([Spacer(1, 6*mm), Paragraph("<b>OPOMBE</b><br/>" + escape(str(invoice[12])).replace("\n", "<br/>"), style["body"])])
    story.extend([Spacer(1, 8*mm), signature_block(company, style)])
    if company.get("invoice_footer"):
        story.extend([Spacer(1, 4*mm), Paragraph(escape(company["invoice_footer"]), style["center"])])
    callback = lambda canvas, document: footer_canvas(canvas, document, company)
    doc.build(story, onFirstPage=callback, onLaterPages=callback)
    return output
