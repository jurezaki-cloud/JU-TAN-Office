"""Items table and totals panel for commercial PDFs."""

from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

from app.pdf.pdf_branding import (
    CONTENT_WIDTH_MM,
    TOTAL_BAR_HEIGHT_MM,
    TOTAL_BAR_WIDTH_MM,
    TOTALS_WIDTH_MM,
    resolve_palette,
)
from app.pdf.pdf_styles import ensure_fonts, styles
from app.utils.money import money


def _money(value) -> str:
    """Slovenian-style EUR display: 1.234,56 €"""
    try:
        amount = float(money(value))
    except (TypeError, ValueError):
        amount = 0.0
    text = f"{amount:,.2f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} €"


def _discount(value) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount == int(amount):
        return f"{int(amount)} %"
    return f"{amount:g} %"


def build_items_table(items: list[dict], options: dict):
    look = styles(options)
    palette = resolve_palette(options)
    _regular, bold = ensure_fonts()
    show_discount = options.get("show_discount", True)

    # Approved reference columns (VAT lives in the totals block, not here).
    headers = ["Šifra", "Artikel", "Količina", "Cena"]
    if show_discount:
        headers.append("Popust")
    headers.append("Skupaj")

    right_cols = {"Količina", "Cena", "Popust", "Skupaj"}
    header_row = [
        Paragraph(text, look["th_right"] if text in right_cols else look["th"])
        for text in headers
    ]
    data = [header_row]
    for item in items:
        row = [
            Paragraph(str(item.get("code") or ""), look["td"]),
            Paragraph(str(item.get("name") or ""), look["td"]),
            Paragraph(str(item.get("quantity") or ""), look["td_right"]),
            Paragraph(_money(item.get("price")), look["td_right"]),
        ]
        if show_discount:
            row.append(Paragraph(_discount(item.get("discount")), look["td_right"]))
        row.append(Paragraph(_money(item.get("total")), look["td_right"]))
        data.append(row)

    if len(data) == 1:
        empty = [Paragraph("Ni postavk", look["td"])] + [""] * (len(headers) - 1)
        data.append(empty)

    total_w = CONTENT_WIDTH_MM * mm
    if show_discount:
        fracs = [0.12, 0.34, 0.11, 0.14, 0.12, 0.17]
    else:
        fracs = [0.14, 0.40, 0.13, 0.15, 0.18]
    widths = [total_w * f for f in fracs]

    table = Table(data, colWidths=widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), palette["charcoal"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), palette["white"]),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("LINEBELOW", (0, 1), (-1, -1), 0.40, palette["light_border"]),
        ("LINEAFTER", (0, 0), (-2, -1), 0.45, palette["light_border"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7.5),
        # MASTER table footprint is taller — grow row/header padding only.
        ("TOPPADDING", (0, 0), (-1, 0), 3.0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3.0),
        ("TOPPADDING", (0, 1), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2.4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [palette["white"], palette["row_alt"]]),
        ("BOX", (0, 0), (-1, -1), 0.40, palette["light_border"]),
        ("ROUNDEDCORNERS", [2.5, 2.5, 0, 0]),
    ]
    table.setStyle(TableStyle(style_cmds))
    return _TableWithAccent(table, palette)


class _TableWithAccent(Flowable):
    """Wraps the items table and paints the green header corner accent."""

    def __init__(self, table: Table, palette: dict):
        super().__init__()
        self.table = table
        self.palette = palette
        self._width = 0
        self._height = 0

    def wrap(self, availWidth, availHeight):
        self._width, self._height = self.table.wrap(availWidth, availHeight)
        return self._width, self._height

    def draw(self):
        self.table.drawOn(self.canv, 0, 0)
        size = 4.4 * mm
        header_top = self._height
        self.canv.setFillColor(self.palette["primary"])
        path = self.canv.beginPath()
        path.moveTo(0, header_top)
        path.lineTo(0, header_top - size)
        path.lineTo(size, header_top)
        path.close()
        self.canv.drawPath(path, fill=1, stroke=0)

    def split(self, availWidth, availHeight):
        parts = self.table.split(availWidth, availHeight)
        if not parts:
            return []
        return [_TableWithAccent(part, self.palette) for part in parts]


def _dominant_vat_rate(items: list[dict] | None) -> str | None:
    rates = []
    for item in items or []:
        try:
            rate = float(item.get("vat") or 0)
        except (TypeError, ValueError):
            continue
        if rate:
            rates.append(rate)
    if not rates:
        return None
    rates.sort()
    best = max(set(rates), key=rates.count)
    if best == int(best):
        return f"{int(best)} %"
    return f"{best:g} %"


class _RoundedPayBar(Flowable):
    """Premium green 'Za plačilo' bar with white label/value."""

    def __init__(self, label: str, value: str, width_mm: float, palette: dict, fonts: tuple[str, str]):
        super().__init__()
        self.label = label
        self.value = value
        self.width_mm = width_mm
        self.palette = palette
        self.regular, self.bold = fonts
        self.height = TOTAL_BAR_HEIGHT_MM * mm

    def wrap(self, availWidth, availHeight):
        self.width = self.width_mm * mm
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.palette["primary"])
        c.roundRect(0, 0, self.width, self.height, 3.4, fill=1, stroke=0)
        c.setFillColor(self.palette["white"])
        c.setFont(self.bold, 12.5)
        c.drawString(3.8 * mm, self.height * 0.32, self.label)
        c.setFont(self.bold, 15.0)
        c.drawRightString(self.width - 3.8 * mm, self.height * 0.28, self.value)


def build_summary(
    subtotal,
    discount,
    vat,
    total,
    options: dict,
    *,
    items: list[dict] | None = None,
):
    """Right-aligned totals with JU-TAN green 'Za plačilo' bar."""
    look = styles(options)
    palette = resolve_palette(options)
    fonts = ensure_fonts()

    rows = [
        [
            Paragraph("Skupaj brez DDV:", look["total_label"]),
            Paragraph(_money(subtotal), look["total_value"]),
        ],
    ]
    if options.get("show_discount", True) and float(discount or 0) != 0:
        rows.append(
            [
                Paragraph("Popust:", look["total_label"]),
                Paragraph(_money(discount), look["total_value"]),
            ]
        )
    if options.get("show_vat", True):
        rate = _dominant_vat_rate(items)
        vat_label = f"DDV ({rate}):" if rate else "DDV:"
        rows.append(
            [
                Paragraph(vat_label, look["total_label"]),
                Paragraph(_money(vat), look["total_value"]),
            ]
        )

    totals = Table(rows, colWidths=[48 * mm, 34 * mm])
    totals.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    pay = _RoundedPayBar("Za plačilo:", _money(total), TOTAL_BAR_WIDTH_MM, palette, fonts)

    stack = Table(
        [[totals], [Spacer(1, 2.0)], [pay]],
        colWidths=[TOTALS_WIDTH_MM * mm],
    )
    stack.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    left_w = (CONTENT_WIDTH_MM - TOTALS_WIDTH_MM) * mm
    wrapper = Table([[Spacer(1, 1), stack]], colWidths=[left_w, TOTALS_WIDTH_MM * mm])
    wrapper.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [Spacer(1, 1.5), wrapper]
