from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from app.pdf.pdf_styles import MUTED, FONT, ensure_fonts


def draw_footer(canvas, doc, footer_text: str):
    ensure_fonts()
    canvas.saveState()
    canvas.setStrokeColor(MUTED)
    canvas.setLineWidth(0.4)
    y = 14 * mm
    canvas.line(15 * mm, y + 8, A4[0] - 15 * mm, y + 8)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    text = (footer_text or "").strip()
    canvas.drawCentredString(A4[0] / 2, y + 2, text)
    canvas.drawRightString(A4[0] - 15 * mm, y + 2, str(doc.page))
    canvas.restoreState()
