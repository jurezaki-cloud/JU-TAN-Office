from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from app.pdf.pdf_branding import resolve_palette
from app.pdf.pdf_styles import PAD, ensure_fonts, styles


def _money(value) -> str:
    try:
        return f"{float(value):,.2f} €".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 €"


def build_items_table(items: list[dict], options: dict):
    look = styles(options)
    palette = resolve_palette(options)
    _regular, bold = ensure_fonts()
    show_vat = options.get("show_vat", True)
    show_discount = options.get("show_discount", True)

    headers = ["Šifra", "Artikel", "Količina", "Cena"]
    if show_vat:
        headers.append("DDV")
    if show_discount:
        headers.append("Popust")
    headers.append("Skupaj")

    header_row = [Paragraph(text, look["th"]) for text in headers]
    data = [header_row]
    for item in items:
        row = [
            Paragraph(str(item.get("code") or ""), look["td"]),
            Paragraph(str(item.get("name") or ""), look["td"]),
            Paragraph(str(item.get("quantity") or ""), look["td_right"]),
            Paragraph(_money(item.get("price")), look["td_right"]),
        ]
        if show_vat:
            row.append(Paragraph(f"{item.get('vat', 0)} %", look["td_right"]))
        if show_discount:
            row.append(Paragraph(str(item.get("discount") or "0"), look["td_right"]))
        row.append(Paragraph(_money(item.get("total")), look["td_right"]))
        data.append(row)

    if len(data) == 1:
        empty = [Paragraph("Ni postavk", look["td"])] + [""] * (len(headers) - 1)
        data.append(empty)

    name_width = 58 * mm
    other = 18 * mm
    widths = [22 * mm, name_width, 20 * mm, 24 * mm]
    if show_vat:
        widths.append(18 * mm)
    else:
        name_width += other
        widths[1] = name_width
    if show_discount:
        widths.append(18 * mm)
    else:
        widths[1] += other
    widths.append(24 * mm)

    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), palette["table_header"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), palette["navy"]),
            ("FONTNAME", (0, 0), (-1, 0), bold),
            ("LINEBELOW", (0, 0), (-1, 0), 1.0, palette["primary"]),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, palette["border"]),
            ("LEFTPADDING", (0, 0), (-1, -1), PAD / 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), PAD / 2),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 1), (-1, -1), palette["white"]),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["white"], palette["table_header"]]),
        ])
    )
    return table


def build_summary(subtotal, discount, vat, total, options: dict):
    """Right-aligned totals panel with accent emphasis on the grand total."""
    look = styles(options)
    palette = resolve_palette(options)
    rows = [
        [Paragraph("Osnova", look["body"]), Paragraph(_money(subtotal), look["body_right"])],
    ]
    if options.get("show_discount", True) and float(discount or 0) != 0:
        rows.append(
            [Paragraph("Popust", look["body"]), Paragraph(_money(discount), look["body_right"])]
        )
    if options.get("show_vat", True):
        rows.append(
            [Paragraph("DDV", look["body"]), Paragraph(_money(vat), look["body_right"])]
        )
    rows.append(
        [
            Paragraph("Skupaj za plačilo", look["total_label"]),
            Paragraph(_money(total), look["total_value"]),
        ]
    )

    table = Table(rows, colWidths=[42 * mm, 38 * mm])
    last = len(rows) - 1
    table.setStyle(
        TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), PAD / 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), PAD / 2),
            ("LINEABOVE", (0, last), (-1, last), 1.1, palette["primary"]),
            ("BACKGROUND", (0, last), (-1, last), palette["table_header"]),
            ("BOX", (0, 0), (-1, -1), 0.4, palette["border"]),
            ("TOPPADDING", (0, last), (-1, last), 7),
            ("BOTTOMPADDING", (0, last), (-1, last), 7),
        ])
    )
    wrapper = Table([[Spacer(1, 1), table]], colWidths=[100 * mm, 80 * mm])
    wrapper.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    return [Spacer(1, PAD), wrapper]
