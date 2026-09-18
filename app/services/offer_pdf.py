from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.document_pdf import (
    LINE, footer_canvas, font_name, header, items_table, parties,
    signature_block, styles, totals_table,
)


def generate_offer_pdf(path, offer, customer, items, company=None):
    """Generate a branded, print-ready A4 offer and return its path."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    company = company or {"company_name": "JU-TAN Studio"}
    font = font_name()
    style = styles(font)
    doc = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
        topMargin=13*mm, bottomMargin=17*mm,
        title=f"Ponudba {offer[1]}", author=company.get("company_name") or "JU-TAN Studio",
    )
    story = [
        header(company, "Ponudba", offer[1], offer[5], font, style), Spacer(1, 7*mm),
        parties(company, customer, [("Datum izdaje", offer[3]), ("Velja do", offer[4] or "—")], style),
        Spacer(1, 8*mm), items_table(items, font), Spacer(1, 6*mm),
        totals_table([
            ["Osnova", f"{offer[6]:.2f} €"], ["Popust", f"-{offer[7]:.2f} €"],
            ["DDV", f"{offer[8]:.2f} €"], ["SKUPAJ", f"{offer[9]:.2f} €"],
        ], font),
    ]
    if offer[10]:
        note = Table([[Paragraph("<b>OPOMBE</b><br/>" + escape(str(offer[10])).replace("\n", "<br/>"), style["body"])]], colWidths=[170*mm])
        note.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), .5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 5*mm), ("TOPPADDING", (0, 0), (-1, -1), 4*mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 4*mm)]))
        story.extend([Spacer(1, 7*mm), note])
    story.extend([Spacer(1, 9*mm), signature_block(company, style)])
    if company.get("invoice_footer"):
        story.extend([Spacer(1, 5*mm), Paragraph(escape(company["invoice_footer"]), style["center"])])
    callback = lambda canvas, document: footer_canvas(canvas, document, company)
    doc.build(story, onFirstPage=callback, onLaterPages=callback)
    return output
