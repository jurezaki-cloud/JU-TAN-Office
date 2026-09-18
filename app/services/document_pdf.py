from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#101A2E")
CYAN = colors.HexColor("#19D3C5")
BLUE = colors.HexColor("#3B82F6")
INK = colors.HexColor("#0B1220")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#DDE5EE")
PALE = colors.HexColor("#F3F7FA")

STATUS_COLORS = {
    "osnutek": (colors.HexColor("#E2E8F0"), colors.HexColor("#334155")),
    "poslano": (colors.HexColor("#DBEAFE"), colors.HexColor("#1D4ED8")),
    "sprejeto": (colors.HexColor("#D1FAE5"), colors.HexColor("#047857")),
    "plačan": (colors.HexColor("#D1FAE5"), colors.HexColor("#047857")),
    "delno plačan": (colors.HexColor("#FEF3C7"), colors.HexColor("#B45309")),
    "neplačan": (colors.HexColor("#FEE2E2"), colors.HexColor("#B91C1C")),
    "zapadel": (colors.HexColor("#FEE2E2"), colors.HexColor("#B91C1C")),
}


def font_name():
    for path in (
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ):
        if path.exists():
            if "JuTanModern" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("JuTanModern", str(path)))
            return "JuTanModern"
    return "Helvetica"


def styles(font):
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("Body", parent=base["Normal"], fontName=font, fontSize=8.5, leading=12, textColor=INK),
        "small": ParagraphStyle("Small", parent=base["Normal"], fontName=font, fontSize=7.2, leading=10, textColor=MUTED),
        "right": ParagraphStyle("Right", parent=base["Normal"], fontName=font, fontSize=8.5, leading=12, alignment=TA_RIGHT, textColor=INK),
        "center": ParagraphStyle("Center", parent=base["Normal"], fontName=font, fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=MUTED),
        "section": ParagraphStyle("Section", parent=base["Heading3"], fontName=font, fontSize=9, leading=12, textColor=NAVY, spaceAfter=4),
    }


def safe_image(path, width, height):
    if not path or not Path(path).is_file():
        return None
    try:
        image = Image(str(path), width=width, height=height, kind="proportional")
        image.hAlign = "LEFT"
        return image
    except Exception:
        return None


def header(company, document_type, number, status, font, style):
    logo = safe_image(company.get("logo_path"), 46*mm, 17*mm)
    brand = logo or Paragraph(
        '<font color="#19D3C5" size="18"><b>JU-TAN</b></font><br/>'
        '<font color="#FFFFFF" size="8">OFFICE</font>', style["body"],
    )
    status_bg, status_fg = STATUS_COLORS.get(str(status).lower(), (CYAN, NAVY))
    badge = Table([[str(status).upper()]], colWidths=[35*mm])
    badge.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (0, 0), (-1, -1), status_fg), ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    right = Table([
        [Paragraph(f'<font color="#8FA3BC" size="8">{escape(document_type.upper())}</font>', style["right"])],
        [Paragraph(f'<font color="#FFFFFF" size="16"><b>{escape(str(number))}</b></font>', style["right"])],
        [badge],
    ], hAlign="RIGHT")
    right.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    table = Table([[brand, right]], colWidths=[91*mm, 79*mm], rowHeights=[31*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 9*mm), ("RIGHTPADDING", (1, 0), (1, 0), 9*mm),
    ]))
    return table


def parties(company, customer, dates, style):
    issuer = [company.get("company_name") or "JU-TAN Studio", company.get("address"),
              f'{company.get("postal_code", "")} {company.get("city", "")}'.strip(),
              company.get("tax_number") and f'Davčna št.: {company["tax_number"]}',
              company.get("email"), company.get("phone")]
    recipient = [customer[1], customer[3], f"{customer[4]} {customer[5]}".strip(),
                 customer[7] and f"Davčna št.: {customer[7]}"]
    date_text = "<br/>".join(f'<font color="#64748B">{escape(k)}:</font> <b>{escape(str(v))}</b>' for k, v in dates)
    table = Table([[
        Paragraph("<b>IZDAJATELJ</b><br/>" + "<br/>".join(escape(str(x)) for x in filter(None, issuer)), style["body"]),
        Paragraph("<b>PREJEMNIK</b><br/>" + "<br/>".join(escape(str(x)) for x in filter(None, recipient)), style["body"]),
        Paragraph(date_text, style["right"]),
    ]], colWidths=[62*mm, 63*mm, 45*mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), .5, LINE), ("INNERGRID", (0, 0), (-1, -1), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5*mm), ("RIGHTPADDING", (0, 0), (-1, -1), 5*mm),
        ("TOPPADDING", (0, 0), (-1, -1), 5*mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 5*mm),
    ]))
    return table


def items_table(items, font):
    rows = [["ŠIFRA", "OPIS", "KOL.", "ENOTA", "CENA", "POPUST", "DDV", "SKUPAJ"]]
    for item in items:
        rows.append([item[2] or "", item[3] or "", f"{item[5]:.2f}", item[6] or "",
                     f"{item[7]:.2f} €", f"{item[8]:.1f} %", f"{item[9]:.1f} %", f"{item[10]:.2f} €"])
    table = Table(rows, repeatRows=1, colWidths=[17*mm,42*mm,15*mm,16*mm,21*mm,18*mm,16*mm,25*mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("LINEBELOW", (0, 0), (-1, 0), 2, CYAN), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 1), (-1, -1), .35, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def totals_table(rows, font):
    table = Table(rows, colWidths=[43*mm, 34*mm], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("TEXTCOLOR", (0, 0), (-1, -2), MUTED),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("BACKGROUND", (0, -1), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white), ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("LEFTPADDING", (0, -1), (-1, -1), 8), ("RIGHTPADDING", (0, -1), (-1, -1), 8),
    ]))
    return table


def sepa_payload(company, amount, reference):
    iban = "".join(str(company.get("iban") or "").split()).upper()
    name = str(company.get("company_name") or "")[:70]
    if not iban or not name or amount <= 0:
        return None
    # EPC QR (SCT): purpose and BIC are optional; invoice number is carried as
    # unstructured remittance information.
    return "\n".join(["BCD", "002", "1", "SCT", "", name, iban,
                      f"EUR{amount:.2f}", "", str(reference)[:140], ""])


def qr_drawing(payload, size=31*mm):
    widget = QrCodeWidget(payload)
    x1, y1, x2, y2 = widget.getBounds()
    drawing = Drawing(size, size, transform=[size/(x2-x1), 0, 0, size/(y2-y1), 0, 0])
    drawing.add(widget)
    return drawing


def payment_block(company, amount, reference, font, style):
    payload = sepa_payload(company, amount, reference)
    if not payload:
        return None
    details = Paragraph(
        '<font color="#19D3C5"><b>SKENIRAJ IN PLAČAJ</b></font><br/>'
        f'<font color="#FFFFFF">Prejemnik: {escape(str(company.get("company_name") or ""))}<br/>'
        f'IBAN: {escape(str(company.get("iban") or ""))}<br/>'
        f'Namen: {escape(str(reference))}<br/><b>Znesek: {amount:.2f} €</b></font>', style["body"])
    table = Table([[qr_drawing(payload), details]], colWidths=[39*mm, 77*mm], rowHeights=[39*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, 0), colors.white), ("BOX", (0, 0), (-1, -1), .5, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 4*mm), ("RIGHTPADDING", (0, 0), (-1, -1), 4*mm),
    ]))
    return table


def signature_block(company, style):
    signature = safe_image(company.get("signature_path"), 40*mm, 17*mm) or Spacer(1, 17*mm)
    stamp = safe_image(company.get("stamp_path"), 30*mm, 25*mm) or Spacer(1, 17*mm)
    table = Table([
        [Paragraph("<b>Pripravil</b>", style["small"]), Paragraph("<b>Podpis in žig</b>", style["small"])],
        [signature, stamp],
        [Paragraph("________________________", style["small"]), Paragraph("________________________", style["small"])],
    ], colWidths=[48*mm, 48*mm], hAlign="RIGHT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    return table


def footer_canvas(canvas, doc, company):
    canvas.saveState()
    width, _ = doc.pagesize
    canvas.setStrokeColor(CYAN); canvas.setLineWidth(1.4)
    canvas.line(doc.leftMargin, 11*mm, width-doc.rightMargin, 11*mm)
    canvas.setFont("Helvetica", 7); canvas.setFillColor(MUTED)
    contact = "  •  ".join(filter(None, [company.get("website"), company.get("email"), company.get("phone")]))
    canvas.drawString(doc.leftMargin, 7*mm, str(contact)[:120])
    canvas.drawRightString(width-doc.rightMargin, 7*mm, f"Stran {doc.page}")
    canvas.restoreState()
