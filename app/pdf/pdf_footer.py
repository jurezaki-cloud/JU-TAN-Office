"""Clean, full-width branded footer for commercial PDF documents."""

from __future__ import annotations

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.pdf.pdf_branding import (
    FOOTER_BAND_MM,
    FOOTER_SLOGAN_HIGHLIGHT,
    FOOTER_SLOGAN_PREFIX,
    LEFT_MARGIN_MM,
    RIGHT_MARGIN_MM,
    TAGLINE,
    THANKS_SUBTITLE,
    resolve_palette,
)
from app.pdf.pdf_styles import ensure_fonts


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
    """Draw a restrained full-bleed footer with a clean professional finish."""
    _ = footer_text, website_url
    font_name, bold = ensure_fonts()
    palette = resolve_palette(options)
    canvas.saveState()

    page_w, page_h = A4
    band_h = FOOTER_BAND_MM * mm

    # Two discreet A4 tri-fold guides for a DL window envelope. Their
    # positions are measured from the top edge: 99 mm and 198 mm.
    canvas.setStrokeColor(palette["primary"])
    canvas.setLineWidth(0.85)
    mark_x1 = 2.5 * mm
    mark_x2 = 7.5 * mm
    for fold_from_top_mm in (99.0, 198.0):
        y = page_h - fold_from_top_mm * mm
        canvas.line(mark_x1, y, mark_x2, y)

    # One continuous full-bleed charcoal foundation. Keeping the top edge
    # horizontal makes the page feel complete and avoids unfinished wedges.
    canvas.setFillColor(palette["charcoal"])
    canvas.rect(0, 0, page_w, band_h, fill=1, stroke=0)

    # Very subtle tonal facets add a modern technical character without
    # competing with the document content.
    base = palette["charcoal"]
    facet_light = (
        min(1, base.red + 0.018),
        min(1, base.green + 0.018),
        min(1, base.blue + 0.016),
    )
    facet_dark = (
        max(0, base.red - 0.018),
        max(0, base.green - 0.016),
        max(0, base.blue - 0.014),
    )

    def _polygon(rgb, points):
        canvas.setFillColorRGB(*rgb)
        path = canvas.beginPath()
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)

    _polygon(
        facet_dark,
        [
            (0, 0),
            (page_w * 0.22, 0),
            (page_w * 0.31, band_h),
            (0, band_h),
        ],
    )
    _polygon(
        facet_light,
        [
            (page_w * 0.22, 0),
            (page_w * 0.50, 0),
            (page_w * 0.43, band_h),
            (page_w * 0.31, band_h),
        ],
    )
    _polygon(
        facet_dark,
        [
            (page_w * 0.72, 0),
            (page_w, 0),
            (page_w, band_h),
            (page_w * 0.86, band_h),
        ],
    )

    # A precise light-grey vector ribbon introduces the document's third brand
    # colour without turning the footer into a collection of loose wedges.
    green_h = 2.2 * mm
    grey_depth = 7.0 * mm
    canvas.setFillColor(palette["footer_grey"])
    grey_ribbon = canvas.beginPath()
    grey_ribbon.moveTo(0, band_h - green_h)
    grey_ribbon.lineTo(page_w * 0.35, band_h - green_h)
    grey_ribbon.lineTo(page_w * 0.29, band_h - green_h - grey_depth)
    grey_ribbon.lineTo(0, band_h - green_h - grey_depth)
    grey_ribbon.close()
    canvas.drawPath(grey_ribbon, fill=1, stroke=0)

    # The uninterrupted green rule locks the whole footer to a clean top edge.
    canvas.setFillColor(palette["primary"])
    canvas.rect(0, band_h - green_h, page_w, green_h, fill=1, stroke=0)

    # Final-page brand rail sits immediately above the green footer edge.
    # It is canvas-anchored so invoice row count cannot make it drift.
    page_no = page_number if page_number is not None else getattr(doc, "page", 1)
    total = page_count if page_count is not None else None
    is_last_page = total is None or page_no == total
    if is_last_page:
        left_x = LEFT_MARGIN_MM * mm
        right_x = page_w - RIGHT_MARGIN_MM * mm

        canvas.setFillColor(palette["charcoal"])
        canvas.setFont(bold, 15.5)
        canvas.drawString(left_x, band_h + 6.3 * mm, "Hvala za zaupanje!")

        canvas.setFillColor(palette["muted"])
        canvas.setFont(font_name, 8.8)
        canvas.drawString(left_x, band_h + 1.8 * mm, THANKS_SUBTITLE)

        canvas.setFillColor(palette["muted"])
        canvas.setFont(font_name, 8.2)
        canvas.drawRightString(right_x, band_h + 6.0 * mm, TAGLINE)

        display_url = (website_url or "").strip()
        display_url = display_url.replace("https://", "").replace("http://", "").rstrip("/")
        if display_url:
            canvas.setFillColor(palette["primary"])
            canvas.setFont(bold, 9.4)
            canvas.drawRightString(right_x, band_h + 1.6 * mm, display_url)

    # Centered brand promise.
    prefix = FOOTER_SLOGAN_PREFIX
    highlight = FOOTER_SLOGAN_HIGHLIGHT
    slogan_size = 9.5
    full_w = stringWidth(prefix + highlight, bold, slogan_size)
    x = (page_w - full_w) / 2.0
    y = band_h * 0.48

    canvas.setFont(bold, slogan_size)
    canvas.setFillColor(palette["white"])
    canvas.drawString(x, y, prefix)
    canvas.setFillColor(palette["primary"])
    canvas.drawString(
        x + stringWidth(prefix, bold, slogan_size),
        y,
        highlight,
    )

    # Quiet, consistently inset page number.
    label = f"{page_no} / {total}" if total else str(page_no)
    canvas.setFillColorRGB(0.80, 0.84, 0.86)
    canvas.setFont(font_name, 7.4)
    canvas.drawRightString(
        page_w - RIGHT_MARGIN_MM * mm,
        4.2 * mm,
        label,
    )

    canvas.restoreState()
