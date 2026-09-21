from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.pdf.pdf_branding import resolve_palette
from app.pdf.pdf_styles import ensure_fonts
from app.utils.vat import DOCUMENT_FOOTER_MESSAGE, WEBSITE_LABEL, WEBSITE_URL


def draw_footer(canvas, doc, footer_text: str = "", *, website_url: str = "", options: dict | None = None):
    """
    Professional two-line document footer with branded accent rule.

    Layout (from bottom):
      page number (right)
      website link (centered)
      thank-you message (centered)
      accent hairline rule
    """
    font_name, _bold = ensure_fonts()
    palette = resolve_palette(options)
    canvas.saveState()

    left = 15 * mm
    right = A4[0] - 15 * mm
    center_x = A4[0] / 2
    baseline = 10 * mm

    message = (footer_text or DOCUMENT_FOOTER_MESSAGE).strip() or DOCUMENT_FOOTER_MESSAGE
    url = (website_url or WEBSITE_URL).strip() or WEBSITE_URL
    link_label = WEBSITE_LABEL

    rule_y = baseline + 14
    canvas.setStrokeColor(palette["primary"])
    canvas.setLineWidth(0.9)
    canvas.line(left, rule_y, right, rule_y)

    canvas.setFillColor(palette["muted"])
    canvas.setFont(font_name, 8)
    canvas.drawCentredString(center_x, baseline + 7, message)

    canvas.setFillColor(palette["navy"])
    canvas.setFont(font_name, 8)
    canvas.drawCentredString(center_x, baseline + 1.5, link_label)

    link_width = stringWidth(link_label, font_name, 8)
    link_height = 9
    x1 = center_x - link_width / 2 - 1
    y1 = baseline + 1.5 - 2
    x2 = center_x + link_width / 2 + 1
    y2 = y1 + link_height
    canvas.linkURL(url, (x1, y1, x2, y2), relative=0)

    canvas.setFillColor(palette["muted"])
    canvas.setFont(font_name, 8)
    canvas.drawRightString(right, baseline + 1.5, str(doc.page))

    canvas.restoreState()
