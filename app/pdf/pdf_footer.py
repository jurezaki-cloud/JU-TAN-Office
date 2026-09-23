"""Geometric document footer drawn on the ReportLab canvas.

Reproduces finalni_desing_racun.png:
  1) light-grey diagonal plane (left)
  2) bright green diagonal band
  3) dark charcoal geometric body with subtle facets
  4) centered slogan + page number ``N / T``
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.pdf.pdf_branding import (
    FOOTER_BAND_MM,
    FOOTER_SLOGAN_HIGHLIGHT,
    FOOTER_SLOGAN_PREFIX,
    RIGHT_MARGIN_MM,
    resolve_palette,
)
from app.pdf.pdf_styles import ensure_fonts
from app.utils.vat import WEBSITE_URL


def draw_footer(
    canvas,
    doc,
    footer_text: str = "",
    *,
    website_url: str = "",
    options: dict | None = None,
    page_number: int | None = None,
    page_count: int | None = None,
):
    """Draw MASTER footer geometry. ``doc`` may be a SimpleDocTemplate or None."""
    _ = footer_text
    font_name, bold = ensure_fonts()
    palette = resolve_palette(options)
    canvas.saveState()

    page_w, _page_h = A4
    band = FOOTER_BAND_MM * mm

    # Rising top edge of charcoal body (MASTER: lower left → higher right).
    left_top = band * 0.45
    mid_top = band * 0.65
    right_top = band * 0.97

    # ------------------------------------------------------------------
    # 1) Light-grey diagonal plane — clearly visible above the green band.
    # ------------------------------------------------------------------
    canvas.setFillColor(palette["footer_grey"])
    grey = canvas.beginPath()
    grey.moveTo(0, left_top + 8.5 * mm)
    grey.lineTo(page_w * 0.45, mid_top + 6.0 * mm)
    grey.lineTo(page_w * 0.82, right_top * 0.60 + 5.0 * mm)
    grey.lineTo(page_w * 0.82, right_top * 0.60 + 0.6 * mm)
    grey.lineTo(page_w * 0.45, mid_top + 1.0 * mm)
    grey.lineTo(0, left_top + 1.6 * mm)
    grey.close()
    canvas.drawPath(grey, fill=1, stroke=0)

    tip = canvas.beginPath()
    tip.moveTo(0, 0)
    tip.lineTo(page_w * 0.22, 0)
    tip.lineTo(page_w * 0.12, left_top + 6.0 * mm)
    tip.lineTo(0, left_top + 5.2 * mm)
    tip.close()
    canvas.drawPath(tip, fill=1, stroke=0)

    # ------------------------------------------------------------------
    # 2) Dark charcoal main body.
    # ------------------------------------------------------------------
    canvas.setFillColor(palette["charcoal"])
    dark = canvas.beginPath()
    dark.moveTo(page_w * 0.03, 0)
    dark.lineTo(page_w, 0)
    dark.lineTo(page_w, right_top)
    dark.lineTo(page_w * 0.55, mid_top + 0.8 * mm)
    dark.lineTo(page_w * 0.28, left_top + 1.6 * mm)
    dark.lineTo(page_w * 0.10, left_top * 0.55)
    dark.lineTo(page_w * 0.03, left_top * 0.15)
    dark.close()
    canvas.drawPath(dark, fill=1, stroke=0)

    # ------------------------------------------------------------------
    # 3) Subtle deterministic facets (low contrast).
    # ------------------------------------------------------------------
    facet_a = (
        max(0, palette["charcoal"].red - 0.012),
        max(0, palette["charcoal"].green - 0.012),
        max(0, palette["charcoal"].blue - 0.010),
    )
    facet_b = (
        max(0, palette["charcoal"].red - 0.020),
        max(0, palette["charcoal"].green - 0.018),
        max(0, palette["charcoal"].blue - 0.015),
    )
    facet_c = (
        min(1, palette["charcoal"].red + 0.010),
        min(1, palette["charcoal"].green + 0.010),
        min(1, palette["charcoal"].blue + 0.008),
    )

    def _poly(rgb, points):
        canvas.setFillColorRGB(*rgb)
        path = canvas.beginPath()
        path.moveTo(*points[0])
        for pt in points[1:]:
            path.lineTo(*pt)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)

    _poly(
        facet_a,
        [
            (page_w * 0.16, 0),
            (page_w * 0.32, 0),
            (page_w * 0.26, left_top + 1.6 * mm),
            (page_w * 0.18, left_top * 0.40),
        ],
    )
    _poly(
        facet_b,
        [
            (page_w * 0.32, 0),
            (page_w * 0.48, 0),
            (page_w * 0.44, mid_top * 0.42),
            (page_w * 0.34, left_top * 0.50),
        ],
    )
    _poly(
        facet_c,
        [
            (page_w * 0.52, 0),
            (page_w * 0.68, 0),
            (page_w * 0.64, mid_top * 0.48),
            (page_w * 0.54, mid_top * 0.26),
        ],
    )
    _poly(
        facet_a,
        [
            (page_w * 0.76, 0),
            (page_w, 0),
            (page_w, right_top * 0.45),
            (page_w * 0.84, mid_top * 0.30),
        ],
    )
    _poly(
        facet_b,
        [
            (page_w * 0.40, mid_top * 0.12),
            (page_w * 0.58, mid_top * 0.20),
            (page_w * 0.52, mid_top * 0.58),
            (page_w * 0.38, mid_top * 0.44),
        ],
    )

    # ------------------------------------------------------------------
    # 4) Green diagonal BAND along charcoal rising edge.
    # ------------------------------------------------------------------
    canvas.setFillColor(palette["primary"])
    strip_h = 3.8 * mm
    strip = canvas.beginPath()
    strip.moveTo(page_w * 0.06, left_top + 0.4 * mm)
    strip.lineTo(page_w * 0.28, left_top + 1.6 * mm)
    strip.lineTo(page_w * 0.55, mid_top + 0.8 * mm)
    strip.lineTo(page_w, right_top)
    strip.lineTo(page_w, right_top + strip_h)
    strip.lineTo(page_w * 0.55, mid_top + 0.8 * mm + strip_h)
    strip.lineTo(page_w * 0.28, left_top + 1.6 * mm + strip_h)
    strip.lineTo(page_w * 0.06, left_top + 0.4 * mm + strip_h)
    strip.close()
    canvas.drawPath(strip, fill=1, stroke=0)

    tip_g = canvas.beginPath()
    tip_g.moveTo(0, left_top + 2.4 * mm)
    tip_g.lineTo(page_w * 0.06, left_top + 0.4 * mm)
    tip_g.lineTo(page_w * 0.06, left_top + 0.4 * mm + strip_h)
    tip_g.lineTo(0, left_top + 2.4 * mm + strip_h * 0.75)
    tip_g.close()
    canvas.drawPath(tip_g, fill=1, stroke=0)

    # ------------------------------------------------------------------
    # 5) Slogan — vertically centered in charcoal body.
    # ------------------------------------------------------------------
    prefix = FOOTER_SLOGAN_PREFIX
    highlight = FOOTER_SLOGAN_HIGHLIGHT
    size = 9.5
    full_w = stringWidth(prefix + highlight, bold, size)
    x = (page_w - full_w) / 2.0
    y = band * 0.28
    canvas.setFillColor(palette["white"])
    canvas.setFont(bold, size)
    canvas.drawString(x, y, prefix)
    x2 = x + stringWidth(prefix, bold, size)
    canvas.setFillColor(palette["primary"])
    canvas.drawString(x2, y, highlight)

    url = (website_url or WEBSITE_URL).strip() or WEBSITE_URL
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    _ = url
    margin_r = RIGHT_MARGIN_MM * mm

    # ------------------------------------------------------------------
    # 6) Page number — MASTER: ``1 / 1`` bottom-right.
    # ------------------------------------------------------------------
    page_no = page_number if page_number is not None else getattr(doc, "page", 1)
    total = page_count if page_count is not None else None
    label = f"{page_no} / {total}" if total else str(page_no)
    canvas.setFillColorRGB(0.92, 0.94, 0.95)
    canvas.setFont(font_name, 7.4)
    canvas.drawRightString(page_w - margin_r, 3.2 * mm, label)

    canvas.restoreState()
