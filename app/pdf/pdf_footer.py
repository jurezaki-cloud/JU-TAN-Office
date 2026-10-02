"""Closing brand footer for commercial PDF documents.

Commercial invoices place the brand composition as a flowable directly under
the closing content (thank-you left, Orbital AI Core centre, service lockup
right) so it belongs to the document. The canvas hook only paints the quiet
page label — and still paints the full brand band for documents that rely on
the page-callback path (e.g. travel orders).
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import getFont, stringWidth
from reportlab.platypus import Flowable

from app.pdf.pdf_branding import (
    CONTENT_WIDTH_MM,
    LEFT_MARGIN_MM,
    RIGHT_MARGIN_MM,
    TAGLINE,
    THANKS_SUBTITLE,
    resolve_palette,
)
from app.pdf.pdf_styles import ensure_fonts

# Page-callback fallback axis (travel orders / legacy). Invoice uses the flowable.
AXIS_Y_MM = 22.0
GUTTER_MM = 4.5

# Flowable band height — halo diameter + quiet vertical air.
COMPOSITION_HEIGHT_MM = 23.0
NOTES_TO_FOOTER_MM = 8.0

THANKS_TITLE = "Hvala za zaupanje!"
THANKS_TITLE_SIZE = 11.8
THANKS_SUB_SIZE = 7.9
THANKS_LINE_GAP_MM = 2.0
THANKS_ACCENT_W_MM = 1.2
THANKS_ACCENT_GAP_MM = 2.7

TAGLINE_SIZE = 6.9
TAGLINE_TRACKING = 0.9
WEBSITE_SIZE = 11.8
LOCKUP_GAP_MM = 2.4

# Orbital AI core — ~20% larger presence vs prior approved baseline.
CORE_OUTER_MM = 10.47
CORE_MID_MM = 7.67
CORE_INNER_MM = 5.17
CORE_NUCLEUS_MM = 3.16
CORE_HALO_MM = 12.54
ORBIT_NODE_MM = 1.05
SPARK_R_MM = 1.95
SPARK_ACCENT_R_MM = 0.69

# Circuit network — thin, precise, mirror-symmetric.
PIN_LENGTH_MM = 2.5
PIN_WIDTH = 1.50
BUS_WIDTH_NEAR = 1.50
BUS_WIDTH_FAR = 0.90
BRANCH_WIDTH = 0.95
BRANCH_TINT = 0.18
BRANCH_LEAD_MM = 2.2
BRANCH_CURVE_MM = 8.2
BRANCH_RISE = 2.55
UPPER_REACH_FRAC = 0.56
LOWER_REACH_FRAC = 0.76
NODE_RING_MM = 1.30
NODE_RING_WIDTH = 1.10
NODE_DOT_MM = 0.62
MID_NODE_MM = 0.56
MIN_NETWORK_SPAN_MM = 48.0

PAGE_LABEL_SIZE = 6.8
PAGE_LABEL_BASELINE_MM = 5.8

# Two discreet A4 tri-fold guides. Positions are measured from the TOP edge
# so the sheet is divided into three equal 99 mm sections for clean folding.
FOLD_GUIDE_FROM_TOP_MM = (99.0, 198.0)
FOLD_GUIDE_LENGTH_MM = 5.0
FOLD_GUIDE_WIDTH = 0.45
FOLD_GUIDE_INSET_MM = 4.0


class BrandFooterBand(Flowable):
    """Premium closing composition — thank-you | Orbital AI Core | brand lockup."""

    def __init__(
        self,
        *,
        website_url: str = "",
        options: dict | None = None,
        width_mm: float = CONTENT_WIDTH_MM,
    ):
        super().__init__()
        self.website_url = website_url or ""
        self.options = options or {}
        self._width = width_mm * mm
        self._height = COMPOSITION_HEIGHT_MM * mm

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        return self._width, self._height

    def draw(self):
        regular, bold = ensure_fonts()
        palette = resolve_palette(self.options)
        axis_y = self._height / 2.0
        gutter = GUTTER_MM * mm
        thanks_right = _draw_thanks(self.canv, palette, regular, bold, 0.0, axis_y)
        lockup_left = _draw_brand_lockup(
            self.canv, palette, regular, bold, self._width, axis_y, self.website_url
        )
        _draw_ai_network(
            self.canv, palette, thanks_right + gutter, lockup_left - gutter, axis_y
        )


def draw_footer(
    canvas,
    doc,
    footer_text: str = "",
    *,
    website_url: str = "",
    options: dict | None = None,
    page_number: int | None = None,
    page_count: int | None = None,
    logo_path: str | Path | None = None,
    draw_brand: bool = True,
):
    """Draw the page label; optionally the brand composition (page-callback path)."""
    _ = footer_text
    _ = logo_path  # Footer no longer shows the JU-TAN logo (header only).
    regular, bold = ensure_fonts()
    palette = resolve_palette(options)
    page_w, _page_h = A4
    left_x = LEFT_MARGIN_MM * mm
    right_x = page_w - RIGHT_MARGIN_MM * mm
    axis_y = AXIS_Y_MM * mm
    gutter = GUTTER_MM * mm

    page_no = page_number if page_number is not None else getattr(doc, "page", 1)
    total = page_count

    canvas.saveState()
    # Quiet folding marks: divide A4 into exact thirds measured from the top.
    canvas.setStrokeColor(_mix(palette["muted"], 0.55))
    canvas.setLineWidth(FOLD_GUIDE_WIDTH)
    x0 = FOLD_GUIDE_INSET_MM * mm
    x1 = x0 + FOLD_GUIDE_LENGTH_MM * mm
    for from_top_mm in FOLD_GUIDE_FROM_TOP_MM:
        y = _page_h - from_top_mm * mm
        canvas.line(x0, y, x1, y)

    if draw_brand and (total is None or page_no == total):
        thanks_right = _draw_thanks(canvas, palette, regular, bold, left_x, axis_y)
        lockup_left = _draw_brand_lockup(
            canvas, palette, regular, bold, right_x, axis_y, website_url
        )
        start = thanks_right + gutter
        end = lockup_left - gutter
        _draw_ai_network(canvas, palette, start, end, axis_y)

    label = f"{page_no} / {total}" if total else str(page_no)
    canvas.setFillColor(_mix(palette["muted"], 0.35))
    canvas.setFont(regular, PAGE_LABEL_SIZE)
    canvas.drawRightString(right_x, PAGE_LABEL_BASELINE_MM * mm, label)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Thank-you lockup (left)
# ---------------------------------------------------------------------------

def _draw_thanks(canvas, palette, regular, bold, left_x: float, axis_y: float) -> float:
    """Premium thank-you stack with a quiet green accent — replaces the footer logo.

    Returns the right edge of the lockup.
    """
    title_w = stringWidth(THANKS_TITLE, bold, THANKS_TITLE_SIZE)
    sub_w = stringWidth(THANKS_SUBTITLE, regular, THANKS_SUB_SIZE)
    text_w = max(title_w, sub_w)

    title_cap = _cap_height(bold, THANKS_TITLE_SIZE)
    sub_cap = _cap_height(regular, THANKS_SUB_SIZE)
    gap = THANKS_LINE_GAP_MM * mm
    block_h = title_cap + gap + sub_cap

    accent_w = THANKS_ACCENT_W_MM * mm
    accent_gap = THANKS_ACCENT_GAP_MM * mm
    text_x = left_x + accent_w + accent_gap

    title_base = axis_y + block_h / 2.0 - title_cap
    sub_base = axis_y - block_h / 2.0

    # Subtle vertical accent — no box, no fill panel.
    accent_top = axis_y + block_h / 2.0
    accent_bot = axis_y - block_h / 2.0
    canvas.setStrokeColor(palette["primary"])
    canvas.setLineWidth(accent_w)
    canvas.setLineCap(1)
    canvas.line(left_x + accent_w / 2.0, accent_bot, left_x + accent_w / 2.0, accent_top)

    canvas.setFillColor(palette["charcoal"])
    canvas.setFont(bold, THANKS_TITLE_SIZE)
    canvas.drawString(text_x, title_base, THANKS_TITLE)

    canvas.setFillColor(palette["muted"])
    canvas.setFont(regular, THANKS_SUB_SIZE)
    canvas.drawString(text_x, sub_base, THANKS_SUBTITLE)

    return text_x + text_w


# ---------------------------------------------------------------------------
# Brand lockup (right)
# ---------------------------------------------------------------------------

def _draw_brand_lockup(canvas, palette, regular, bold, right_x, axis_y, website_url) -> float:
    """Tracked service tagline over the website, right-aligned and centred on the axis.

    Returns the left edge of the lockup.
    """
    display = (website_url or "").strip()
    display = display.replace("https://", "").replace("http://", "").rstrip("/")

    tag_w = stringWidth(TAGLINE, regular, TAGLINE_SIZE) + TAGLINE_TRACKING * (len(TAGLINE) - 1)
    web_w = stringWidth(display, bold, WEBSITE_SIZE) if display else 0.0
    tag_cap = _cap_height(regular, TAGLINE_SIZE)
    web_cap = _cap_height(bold, WEBSITE_SIZE)

    if display:
        block_h = tag_cap + LOCKUP_GAP_MM * mm + web_cap
    else:
        block_h = tag_cap
    tag_base = axis_y + block_h / 2.0 - tag_cap
    web_base = axis_y - block_h / 2.0

    # Character spacing is graphics state and outlives the text object, so the
    # tracked tagline gets its own state scope.
    canvas.saveState()
    text = canvas.beginText(right_x - tag_w, tag_base)
    text.setFont(regular, TAGLINE_SIZE)
    text.setCharSpace(TAGLINE_TRACKING)
    words = TAGLINE.split("|")
    for index, word in enumerate(words):
        if index:
            text.setFillColor(palette["primary"])
            text.textOut("|")
        text.setFillColor(palette["muted"])
        text.textOut(word)
    canvas.drawText(text)
    canvas.restoreState()

    if display:
        canvas.setFillColor(palette["primary"])
        canvas.setFont(bold, WEBSITE_SIZE)
        canvas.drawRightString(right_x, web_base, display)
        configured = (website_url or "").strip()
        is_web = configured.lower().startswith(("http://", "https://"))
        url = configured if is_web else f"https://{display}"
        canvas.linkURL(
            url,
            (right_x - web_w, web_base - 0.25 * WEBSITE_SIZE, right_x, web_base + web_cap + 1.0),
            relative=0,
            thickness=0,
        )
    return right_x - max(tag_w, web_w)


def _cap_height(font_name: str, size: float) -> float:
    face = getattr(getFont(font_name), "face", None)
    cap = getattr(face, "capHeight", 0) or 700
    return cap / 1000.0 * size


# ---------------------------------------------------------------------------
# Premium AI / digital network hero (centre)
# ---------------------------------------------------------------------------

def _draw_ai_network(canvas, palette, x_start: float, x_end: float, cy: float) -> None:
    """Mirror-symmetric digital network flowing out of the orbital AI core."""
    if x_end <= x_start:
        return
    cx = (x_start + x_end) / 2.0
    span = x_end - x_start
    if span < MIN_NETWORK_SPAN_MM * mm:
        _draw_ai_core(canvas, palette, cx, cy)
        return

    green = palette["primary"]
    charcoal = palette["charcoal"]
    branch = _mix(green, BRANCH_TINT)
    half = span / 2.0
    pin = PIN_LENGTH_MM * mm
    ring = NODE_RING_MM * mm
    outer = CORE_OUTER_MM * mm
    # Pins begin outside the orbital ring so nothing crosses the core.
    pin_start = outer + ORBIT_NODE_MM * mm * 0.15
    pin_end = outer + pin
    lead = pin_end + BRANCH_LEAD_MM * mm
    curve = BRANCH_CURVE_MM * mm
    pitch = 3.35 * mm

    canvas.setLineCap(1)
    canvas.setLineJoin(1)

    for side in (-1, 1):
        near = cx + side * pin_end
        far = cx + side * (half - ring)

        # Main bus — solid tapered ribbon (prints cleanly, no hairline loss).
        bus = canvas.beginPath()
        bus.moveTo(near, cy + BUS_WIDTH_NEAR / 2)
        bus.lineTo(far, cy + BUS_WIDTH_FAR / 2)
        bus.lineTo(far, cy - BUS_WIDTH_FAR / 2)
        bus.lineTo(near, cy - BUS_WIDTH_NEAR / 2)
        bus.close()
        canvas.setFillColor(green)
        canvas.drawPath(bus, stroke=0, fill=1)

        # Primary pin from the east/west orbit node into the bus.
        canvas.setStrokeColor(green)
        canvas.setLineWidth(PIN_WIDTH)
        canvas.line(cx + side * pin_start, cy, near, cy)

        # Upper / lower neural branches — leave cleanly outside the ring.
        for lift, reach_frac in ((1, UPPER_REACH_FRAC), (-1, LOWER_REACH_FRAC)):
            reach = min(half * reach_frac, half - 7 * mm)
            y_pin = cy + lift * pitch
            y_run = cy + lift * BRANCH_RISE * pitch
            branch_start = cx + side * pin_start

            canvas.setStrokeColor(green)
            canvas.setLineWidth(PIN_WIDTH * 0.9)
            canvas.line(branch_start, y_pin, cx + side * (pin_end * 0.92), y_pin)

            canvas.setStrokeColor(branch)
            canvas.setLineWidth(BRANCH_WIDTH)
            path = canvas.beginPath()
            path.moveTo(cx + side * (pin_end * 0.92), y_pin)
            path.lineTo(cx + side * lead, y_pin)
            path.curveTo(
                cx + side * (lead + curve / 2), y_pin,
                cx + side * (lead + curve / 2), y_run,
                cx + side * (lead + curve), y_run,
            )
            path.lineTo(cx + side * reach, y_run)
            canvas.drawPath(path, stroke=1, fill=0)
            canvas.setFillColor(branch)
            canvas.circle(cx + side * reach, y_run, NODE_DOT_MM * mm, stroke=0, fill=1)

            # Tiny via where the branch leaves the pin field.
            canvas.setFillColor(green)
            canvas.circle(branch_start, y_pin, 0.40 * mm, stroke=0, fill=1)

        # Mid-span data node on the bus.
        mid_x = cx + side * (pin_end + (half - ring - pin_end) * 0.40)
        canvas.setFillColor(palette["white"])
        canvas.setStrokeColor(green)
        canvas.setLineWidth(0.95)
        canvas.circle(mid_x, cy, MID_NODE_MM * mm, stroke=1, fill=1)

        # Terminal ring — soft hand-off toward thanks / lockup.
        canvas.setStrokeColor(green)
        canvas.setLineWidth(NODE_RING_WIDTH)
        canvas.setFillColor(palette["white"])
        canvas.circle(cx + side * half, cy, ring, stroke=1, fill=1)
        canvas.setFillColor(green)
        canvas.circle(cx + side * half, cy, NODE_DOT_MM * mm * 0.88, stroke=0, fill=1)

    # Quiet charcoal micro-traces for depth (secondary only, near the core).
    canvas.setStrokeColor(_mix(charcoal, 0.80))
    canvas.setLineWidth(0.60)
    for side in (-1, 1):
        canvas.line(
            cx + side * (outer + 1.0 * mm),
            cy + 1.35 * mm,
            cx + side * (outer + 5.0 * mm),
            cy + 1.35 * mm,
        )
        canvas.line(
            cx + side * (outer + 1.0 * mm),
            cy - 1.35 * mm,
            cx + side * (outer + 4.0 * mm),
            cy - 1.35 * mm,
        )

    _draw_ai_core(canvas, palette, cx, cy)


def _draw_ai_core(canvas, palette, cx: float, cy: float) -> None:
    """Orbital AI nucleus — layered rings, orbit nodes, charcoal core, AI spark."""
    green = palette["primary"]
    charcoal = palette["charcoal"]
    white = palette["white"]
    soft_green = _mix(green, 0.86)

    halo = CORE_HALO_MM * mm
    outer = CORE_OUTER_MM * mm
    mid = CORE_MID_MM * mm
    inner = CORE_INNER_MM * mm
    nucleus = CORE_NUCLEUS_MM * mm

    # Soft halo — presence without a grey band or fill.
    canvas.setStrokeColor(soft_green)
    canvas.setLineWidth(1.25)
    canvas.circle(cx, cy, halo, stroke=1, fill=0)

    # Outer orbital ring.
    canvas.setStrokeColor(green)
    canvas.setLineWidth(1.55)
    canvas.circle(cx, cy, outer, stroke=1, fill=0)

    # Mid charcoal ring — depth and contrast for print / grayscale.
    canvas.setStrokeColor(charcoal)
    canvas.setLineWidth(1.15)
    canvas.circle(cx, cy, mid, stroke=1, fill=0)

    # Inner green ring.
    canvas.setStrokeColor(green)
    canvas.setLineWidth(1.05)
    canvas.circle(cx, cy, inner, stroke=1, fill=0)

    # Compact charcoal nucleus — circular, not a chip package.
    canvas.setFillColor(charcoal)
    canvas.circle(cx, cy, nucleus, stroke=0, fill=1)

    # Soft inset bevel for a machined, premium feel.
    canvas.setStrokeColor(_mix(charcoal, 0.22))
    canvas.setLineWidth(0.55)
    canvas.circle(cx, cy, nucleus * 0.72, stroke=1, fill=0)

    # Cardinal orbit nodes — deliberate connection points for the network.
    node_r = ORBIT_NODE_MM * mm
    for angle_deg in (0, 90, 180, 270):
        rad = math.radians(angle_deg)
        nx = cx + math.cos(rad) * outer
        ny = cy + math.sin(rad) * outer
        canvas.setFillColor(white)
        canvas.setStrokeColor(green)
        canvas.setLineWidth(1.05)
        canvas.circle(nx, ny, node_r, stroke=1, fill=1)
        canvas.setFillColor(green)
        canvas.circle(nx, ny, node_r * 0.40, stroke=0, fill=1)

    # Diagonal micro-nodes on the mid ring — secondary rhythm only.
    for angle_deg in (45, 135, 225, 315):
        rad = math.radians(angle_deg)
        nx = cx + math.cos(rad) * mid
        ny = cy + math.sin(rad) * mid
        canvas.setFillColor(_mix(charcoal, 0.15))
        canvas.circle(nx, ny, 0.38 * mm, stroke=0, fill=1)

    # Primary white AI spark with a small green accent.
    canvas.setFillColor(white)
    _spark(canvas, cx - 0.14 * mm, cy - 0.09 * mm, SPARK_R_MM * mm)
    canvas.setFillColor(green)
    _spark(canvas, cx + nucleus * 0.48, cy + nucleus * 0.42, SPARK_ACCENT_R_MM * mm)


def _spark(canvas, x: float, y: float, r: float) -> None:
    """Four-point AI spark with concave sides."""
    k = 0.18 * r
    path = canvas.beginPath()
    path.moveTo(x, y + r)
    path.curveTo(x, y + k, x + k, y, x + r, y)
    path.curveTo(x + k, y, x, y - k, x, y - r)
    path.curveTo(x, y - k, x - k, y, x - r, y)
    path.curveTo(x - k, y, x, y + k, x, y + r)
    path.close()
    canvas.drawPath(path, stroke=0, fill=1)


def _mix(color, toward_white: float) -> Color:
    """Solid tint of ``color`` (no transparency, so it prints predictably)."""
    t = max(0.0, min(1.0, toward_white))
    return Color(
        color.red + (1 - color.red) * t,
        color.green + (1 - color.green) * t,
        color.blue + (1 - color.blue) * t,
    )
