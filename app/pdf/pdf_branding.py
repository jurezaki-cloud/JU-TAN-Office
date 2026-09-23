"""Document branding — palette, page geometry, and reusable vector helpers."""

from __future__ import annotations

import re
import shutil
from pathlib import Path as FsPath

from reportlab.graphics.shapes import Circle, Drawing, Line, Path as RlPath, Rect
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Flowable

from app.core.constants import DATA_DIR
from app.database.company_repository import (
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    DEFAULT_TABLE_HEADER,
)
from app.theme.colors import LightColors

_HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")

# ---------------------------------------------------------------------------
# Page geometry (A4 portrait) — MASTER-relative layout map
# Normalized from invoice-reference.png / qa-side-by-side.png → A4 mm.
# ---------------------------------------------------------------------------
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = A4
PAGE_WIDTH_MM = PAGE_WIDTH_PT / mm
PAGE_HEIGHT_MM = PAGE_HEIGHT_PT / mm

# MASTER content grid ≈ x 0.059–0.962 of page → balanced side margins.
LEFT_MARGIN_MM = 10.0
RIGHT_MARGIN_MM = 10.0
# MASTER logo ink top ≈ 0.039 — tight top air for dominant brand group.
TOP_MARGIN_MM = 4.0
CONTENT_LEFT_MM = LEFT_MARGIN_MM
CONTENT_RIGHT_MM = PAGE_WIDTH_MM - RIGHT_MARGIN_MM
CONTENT_WIDTH_MM = PAGE_WIDTH_MM - LEFT_MARGIN_MM - RIGHT_MARGIN_MM  # ≈ 190
# Post-separator → identity; MASTER sep ≈ identity top (near-zero air).
SECTION_SPACING_MM = 4.0
# Header body → separator. MASTER sep ≈ 0.202 (was ~7 pt / too high).
HEADER_TO_SEPARATOR_MM = 9.5

# MASTER footer_top ≈ 0.896 → branded band (~33 mm). Charcoal fills most of it.
FOOTER_BAND_MM = 33.0
FOOTER_RESERVED_MM = 33.0

# MASTER logo group ≈ 0.52 × 0.11 of page (preserve asset aspect).
LOGO_MAX_WIDTH_MM = 126.0
LOGO_MAX_HEIGHT_MM = 36.0

# MASTER customer card ≈ 0.46–0.52 wide; scale with content (no empty lower band).
CUSTOMER_CARD_WIDTH_MM = 99.0
CUSTOMER_ICON_MM = 22.0
CUSTOMER_CARD_PAD_PT = 10.5

TOTALS_WIDTH_MM = 80.0
TOTAL_BAR_WIDTH_MM = 76.0
TOTAL_BAR_HEIGHT_MM = 12.5

# MASTER QR side ≈ 0.13 of page width; keep quiet zone / scannable UPN modules.
# UPN QR: version 15 is 77 modules + mandatory 4-module quiet zone on each side.
# ZBS module size is 0.42333 mm, so the complete symbol is about 35.98 mm.
QR_SIDE_MM = 85 * 0.42333
PAYMENT_COL_WIDTH_MM = 80.0
BANK_ICON_MM = 14.5

WATERMARK_WIDTH_MM = 120.0
WATERMARK_HEIGHT_MM = 55.0
THANKS_RESERVE_MM = 20.0

# Deterministic one-page gaps from MASTER landmarks (not remaining frame space).
# RAČUN MASTER y0 ≈ 0.229 — inset within the identity row (card top stays).
RACUN_TOP_INSET_MM = 2.8
# Keep table top near MASTER after taller customer card.
IDENTITY_TO_TABLE_MM = 0.8
# Shrink when upper content grows so UPN/payment Y stays frozen (~0.70).
TOTALS_TO_PAYMENT_GAP_MM = 10.5
THANKS_BEFORE_MM = 1.2

SIGNATURE_WIDTH_MM = 50.0
SIGNATURE_HEIGHT_MM = 18.0

# Wordmark starts ~29% into the logo asset; tagline sits under JU-TAN only.
LOGO_MONOGRAM_FRAC = 0.29
# Official logo PNGs carry bottom padding — pull tagline into that void (MASTER).
LOGO_TAGLINE_PULL_FRAC = 0.85
# MASTER tagline tracking (ReportLab charSpace units).
TAGLINE_CHAR_SPACE = 1.15

# ---------------------------------------------------------------------------
# MASTER normalized landmarks from finalni_desing_racun.png
# (fraction of page height from top). Used for one-page vertical grid.
# ---------------------------------------------------------------------------
MASTER_LOGO_TOP = 0.039
MASTER_LOGO_BOTTOM = 0.165
MASTER_SEPARATOR_Y = 0.202
MASTER_CUSTOMER_TOP = 0.195
MASTER_CUSTOMER_BOTTOM = 0.415
MASTER_RACUN_TOP = 0.229
MASTER_IDENTITY_TOP = 0.195
MASTER_IDENTITY_BOTTOM = 0.415
MASTER_TABLE_TOP = 0.387
MASTER_TABLE_BOTTOM = 0.533
MASTER_TOTALS_TOP = 0.595
MASTER_TOTALS_BOTTOM = 0.650
MASTER_PAYMENT_TOP = 0.698
MASTER_PAYMENT_BOTTOM = 0.717
MASTER_THANKS_TOP = 0.820
MASTER_FOOTER_TOP = 0.889


def master_y_mm(frac: float) -> float:
    """Map a MASTER normalized Y landmark to A4 millimetres from page top."""
    return float(frac) * PAGE_HEIGHT_MM

# ---------------------------------------------------------------------------
# Brand palette (approved JU-TAN commercial look)
# ---------------------------------------------------------------------------
BRAND_GREEN = "#00C96B"
CHARCOAL = "#121B20"
TEXT_MAIN = "#111827"
TEXT_SECONDARY = "#64748B"
LIGHT_BORDER = "#D9E1E5"
LIGHT_GREEN = "#F2FBF6"
ROW_ALT = "#F7FAFB"
FOOTER_GREY = "#E8EEF0"
TAGLINE = "PROGRAMI | REŠITVE | PODPORA"
THANKS_SUBTITLE = "Skupaj gradimo boljše rešitve."
FOOTER_SLOGAN_PREFIX = "VAŠ PARTNER ZA "
FOOTER_SLOGAN_HIGHLIGHT = "DIGITALNO PRIHODNOST"
SIGNATURE_ROLE_DEFAULT = "Direktorica"


def normalize_hex(value: str, fallback: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return fallback
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if not _HEX.match(raw):
        return fallback
    return "#" + raw[1:].upper()


def _hex(value: str) -> HexColor:
    return HexColor(normalize_hex(value, "#000000"))


def with_alpha(color: Color, alpha: float) -> Color:
    """Return a Color with the given alpha (ReportLab 0–1)."""
    return Color(color.red, color.green, color.blue, alpha)


def resolve_palette(options: dict | None = None) -> dict:
    """Resolve ReportLab colors from PDF options (DB branding) with safe defaults."""
    colors = (options or {}).get("colors") or {}
    primary = normalize_hex(colors.get("primary"), DEFAULT_PRIMARY)
    accent = normalize_hex(colors.get("accent"), DEFAULT_ACCENT)
    table_header = normalize_hex(colors.get("table_header"), DEFAULT_TABLE_HEADER)
    return {
        # Legacy keys used across the PDF stack
        "navy": _hex(primary),
        "primary": _hex(accent),
        "muted": _hex(TEXT_SECONDARY),
        "border": _hex(LIGHT_BORDER),
        "table_header": _hex(table_header),
        "surface": HexColor(LightColors.SURFACE),
        "white": white,
        "primary_hex": primary,
        "accent_hex": accent,
        "table_header_hex": table_header,
        # Approved visual-identity tokens
        "charcoal": _hex(CHARCOAL),
        "text": _hex(TEXT_MAIN),
        "light_green": _hex(LIGHT_GREEN),
        "light_border": _hex(LIGHT_BORDER),
        "row_alt": _hex(ROW_ALT),
        "footer_grey": _hex(FOOTER_GREY),
        "on_primary": white,
        "brand_green": _hex(BRAND_GREEN),
    }


def branding_dir() -> FsPath:
    folder = DATA_DIR / "branding"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def archive_branding_asset(source: str, kind: str) -> str:
    """
    Copy a user-selected image into DATA_DIR/branding for stable PDF paths.

    kind: logo | signature | stamp
    Returns the archived path string, or "" if source is empty/missing.
    """
    if not source:
        return ""
    src = FsPath(source)
    if not src.exists() or not src.is_file():
        return str(source)
    suffix = src.suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        suffix = ".png"
    target = branding_dir() / f"company_{kind}{suffix}"
    try:
        from app.core.security import ensure_inside

        target = ensure_inside(target, branding_dir())
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
        return str(target)
    except Exception:
        return str(source)


# ---------------------------------------------------------------------------
# Vector icons
# ---------------------------------------------------------------------------

def contact_phone_icon(palette: dict, size: float = 9.5) -> Drawing:
    """Solid white handset on green circle (MASTER contact glyph)."""
    d = Drawing(size, size)
    d.add(Circle(size / 2, size / 2, size / 2, fillColor=palette["primary"], strokeColor=None))
    # Classic filled handset (circle + stem).
    d.add(
        Rect(
            size * 0.28,
            size * 0.18,
            size * 0.22,
            size * 0.62,
            fillColor=palette["white"],
            strokeColor=None,
            rx=1.4,
            ry=1.4,
        )
    )
    d.add(
        Rect(
            size * 0.28,
            size * 0.56,
            size * 0.44,
            size * 0.22,
            fillColor=palette["white"],
            strokeColor=None,
            rx=1.4,
            ry=1.4,
        )
    )
    return d


def contact_email_icon(palette: dict, size: float = 9.5) -> Drawing:
    """Solid white envelope on green circle (MASTER contact glyph)."""
    d = Drawing(size, size)
    d.add(Circle(size / 2, size / 2, size / 2, fillColor=palette["primary"], strokeColor=None))
    d.add(
        Rect(
            size * 0.20,
            size * 0.28,
            size * 0.60,
            size * 0.42,
            fillColor=palette["white"],
            strokeColor=None,
            rx=0.6,
            ry=0.6,
        )
    )
    path = RlPath(fillColor=palette["primary"], strokeColor=None)
    path.moveTo(size * 0.20, size * 0.70)
    path.lineTo(size * 0.50, size * 0.46)
    path.lineTo(size * 0.80, size * 0.70)
    path.closePath()
    d.add(path)
    return d


def contact_web_icon(palette: dict, size: float = 9.5) -> Drawing:
    """Solid white globe on green circle (MASTER contact glyph)."""
    d = Drawing(size, size)
    d.add(Circle(size / 2, size / 2, size / 2, fillColor=palette["primary"], strokeColor=None))
    d.add(
        Circle(
            size / 2,
            size / 2,
            size * 0.28,
            fillColor=palette["white"],
            strokeColor=None,
        )
    )
    d.add(
        Circle(
            size / 2,
            size / 2,
            size * 0.28,
            fillColor=None,
            strokeColor=palette["primary"],
            strokeWidth=0.9,
        )
    )
    d.add(
        Line(
            size * 0.22,
            size / 2,
            size * 0.78,
            size / 2,
            strokeColor=palette["primary"],
            strokeWidth=0.8,
        )
    )
    d.add(
        Line(
            size / 2,
            size * 0.22,
            size / 2,
            size * 0.78,
            strokeColor=palette["primary"],
            strokeWidth=0.8,
        )
    )
    return d


def customer_people_icon(palette: dict, size: float = 32) -> Drawing:
    """Green tile with thin white OUTLINE two-person icon (MASTER — not filled)."""
    d = Drawing(size, size)
    d.add(
        Rect(
            0,
            0,
            size,
            size,
            fillColor=palette["primary"],
            strokeColor=None,
            rx=2.6,
            ry=2.6,
        )
    )
    ink = palette["white"]
    # MASTER: delicate outline strokes (never filled heads/bodies).
    sw = max(size * 0.055, 0.95)

    def _bust(cx: float, scale: float = 1.0):
        hr = size * 0.118 * scale
        hy = size * 0.66
        d.add(Circle(cx, hy, hr, fillColor=None, strokeColor=ink, strokeWidth=sw))
        bw = size * 0.32 * scale
        by = size * 0.16
        top = size * 0.46
        path = RlPath(fillColor=None, strokeColor=ink, strokeWidth=sw)
        path.moveTo(cx - bw * 0.55, by)
        path.curveTo(cx - bw * 0.55, top * 0.72, cx - bw * 0.18, top, cx, top)
        path.curveTo(cx + bw * 0.18, top, cx + bw * 0.55, top * 0.72, cx + bw * 0.55, by)
        d.add(path)

    # Rear figure slightly smaller / left-back (MASTER group glyph).
    _bust(size * 0.35, 0.88)
    _bust(size * 0.63, 1.00)
    return d


def bank_icon(palette: dict, size: float = 38) -> Drawing:
    """Pale-green rounded square with green bank/building glyph (~13–14 mm)."""
    d = Drawing(size, size)
    d.add(
        Rect(
            0,
            0,
            size,
            size,
            fillColor=palette["light_green"],
            strokeColor=None,
            rx=3.2,
            ry=3.2,
        )
    )
    g = palette["primary"]
    # Pediment / roof
    roof = RlPath(fillColor=g, strokeColor=None)
    roof.moveTo(size * 0.16, size * 0.62)
    roof.lineTo(size * 0.50, size * 0.82)
    roof.lineTo(size * 0.84, size * 0.62)
    roof.closePath()
    d.add(roof)
    # Columns
    for x in (0.24, 0.40, 0.56, 0.72):
        d.add(Rect(size * x, size * 0.30, size * 0.08, size * 0.32, fillColor=g, strokeColor=None))
    # Base
    d.add(Rect(size * 0.18, size * 0.20, size * 0.64, size * 0.08, fillColor=g, strokeColor=None))
    return d


def extract_signer_name(company_name: str) -> str:
    """Best-effort person name from 'JU-TAN studio, Tanja Hrup s.p.'."""
    raw = (company_name or "").strip()
    if "," in raw:
        tail = raw.split(",", 1)[1].strip()
        tail = re.sub(r"\s+s\.?\s*p\.?\s*$", "", tail, flags=re.IGNORECASE).strip()
        if tail:
            return tail
    return raw


# ---------------------------------------------------------------------------
# Decorative flowables
# ---------------------------------------------------------------------------

class HeaderSeparator(Flowable):
    """Thin grey rule with a short green left accent and a finishing tip on the right."""

    def __init__(self, width_mm: float, palette: dict, accent_mm: float = 22):
        super().__init__()
        self.width_mm = width_mm
        self.accent_mm = accent_mm
        self.palette = palette
        self.height = 2.2 * mm

    def wrap(self, availWidth, availHeight):
        self.width = self.width_mm * mm
        return self.width, self.height

    def draw(self):
        y = self.height / 2
        accent_w = self.accent_mm * mm
        tip = 2.4 * mm
        self.canv.setStrokeColor(self.palette["primary"])
        self.canv.setLineWidth(1.45)
        self.canv.line(0, y, accent_w, y)
        self.canv.setStrokeColor(self.palette["light_border"])
        self.canv.setLineWidth(0.60)
        self.canv.line(accent_w, y, self.width - tip, y)
        self.canv.setStrokeColor(self.palette["primary"])
        self.canv.setLineWidth(1.25)
        self.canv.line(self.width - tip, y, self.width, y)


class JTWatermark(Flowable):
    """Pale horizontal JT monogram behind payment — MASTER-like, left-clipped.

    Reports zero flow height so it never inflates the story / triggers a
    KeepTogether page-break. Drawn extending upward from the current baseline.
    """

    def __init__(self, width_mm: float, height_mm: float, palette: dict):
        super().__init__()
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.palette = palette

    def wrap(self, availWidth, availHeight):
        self.width = self.width_mm * mm
        # Zero flow height — visual extent is painted upward in draw().
        self.height = 0
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        # MASTER: pale but readable (~5.5%), large, horizontal, partly clipped at left.
        ink = with_alpha(self.palette["charcoal"], 0.055)
        accent = with_alpha(self.palette["primary"], 0.045)
        c.setFillColor(ink)
        c.setStrokeColor(ink)
        w = self.width * 1.18
        h = self.height_mm * mm * 0.88
        x = -self.width * 0.22
        y = 2 * mm
        stroke = max(min(w, h) * 0.11, 3.2)
        c.setLineWidth(stroke)
        c.setLineCap(1)
        c.setLineJoin(1)
        stem_x = x + w * 0.42
        c.line(stem_x, y + h * 0.14, stem_x, y + h * 0.82)
        path = c.beginPath()
        path.moveTo(stem_x, y + h * 0.38)
        path.curveTo(
            stem_x,
            y + h * 0.00,
            x + w * 0.04,
            y + h * 0.00,
            x + w * 0.08,
            y + h * 0.28,
        )
        c.drawPath(path, fill=0, stroke=1)
        c.setFillColor(accent)
        bar = c.beginPath()
        bar.moveTo(x + w * 0.30, y + h * 0.78)
        bar.lineTo(x + w * 0.98, y + h * 0.90)
        bar.lineTo(x + w * 0.94, y + h * 0.70)
        bar.lineTo(x + w * 0.28, y + h * 0.60)
        bar.close()
        c.drawPath(bar, fill=1, stroke=0)
        c.restoreState()


class PaymentWithWatermark(Flowable):
    """Payment/QR row with JT watermark painted behind (no extra flow height)."""

    def __init__(self, content: Flowable, watermark: JTWatermark):
        super().__init__()
        self.content = content
        self.watermark = watermark
        self._width = 0
        self._height = 0

    def wrap(self, availWidth, availHeight):
        self._width, self._height = self.content.wrap(availWidth, availHeight)
        self.watermark.wrap(self._width, self._height)
        return self._width, self._height

    def draw(self):
        self.watermark.drawOn(self.canv, 0, 0)
        self.content.drawOn(self.canv, 0, 0)


class VerticalGreenRule(Flowable):
    """Thin vertical brand accent between payment details and QR."""

    def __init__(self, height_mm: float, palette: dict):
        super().__init__()
        self.height_mm = height_mm
        self.palette = palette
        self.width = 1.0 * mm

    def wrap(self, availWidth, availHeight):
        self.height = self.height_mm * mm
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.palette["primary"])
        self.canv.setLineWidth(0.9)
        self.canv.line(self.width / 2, 0, self.width / 2, self.height)


class SpacedTagline(Flowable):
    """MASTER logo/brand tagline with deliberate letter spacing."""

    def __init__(
        self,
        text: str,
        width: float,
        *,
        font_name: str,
        font_size: float,
        color,
        char_space: float = TAGLINE_CHAR_SPACE,
        align: str = "center",
    ):
        super().__init__()
        self.text = text
        self._width = width
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.char_space = char_space
        self.align = align
        self.height = font_size * 1.25

    def wrap(self, availWidth, availHeight):
        self.width = self._width
        return self.width, self.height

    def draw(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        c = self.canv
        c.saveState()
        c.setFillColor(self.color)
        c.setFont(self.font_name, self.font_size)
        # Manual tracking — ReportLab Canvas has no setCharSpacing API.
        widths = [stringWidth(ch, self.font_name, self.font_size) for ch in self.text]
        total = sum(widths) + self.char_space * max(len(self.text) - 1, 0)
        if self.align == "right":
            x = self.width - total
        elif self.align == "left":
            x = 0
        else:
            x = max((self.width - total) / 2.0, 0)
        cursor = x
        for ch, w in zip(self.text, widths):
            c.drawString(cursor, 1.0, ch)
            cursor += w + self.char_space
        c.restoreState()


class CustomerCard(Flowable):
    """MASTER customer card: pale wash, rounded green border, icon + text."""

    def __init__(self, content: Flowable, width_mm: float, palette: dict, radius: float = 4.5):
        super().__init__()
        self.content = content
        self.width_mm = width_mm
        self.palette = palette
        self.radius = radius
        self._width = 0
        self._height = 0

    def wrap(self, availWidth, availHeight):
        pad = CUSTOMER_CARD_PAD_PT
        inner_w = self.width_mm * mm - 2 * pad
        cw, ch = self.content.wrap(inner_w, availHeight)
        self._width = self.width_mm * mm
        self._height = ch + 2 * pad
        self._pad = pad
        return self._width, self._height

    def draw(self):
        from reportlab.lib.colors import Color

        c = self.canv
        border = Color(
            self.palette["primary"].red * 0.40 + 0.60,
            self.palette["primary"].green * 0.40 + 0.60,
            self.palette["primary"].blue * 0.40 + 0.60,
        )
        wash = Color(
            self.palette["primary"].red * 0.055 + 0.945,
            self.palette["primary"].green * 0.055 + 0.945,
            self.palette["primary"].blue * 0.055 + 0.945,
        )
        c.saveState()
        c.setFillColor(wash)
        c.setStrokeColor(border)
        c.setLineWidth(1.05)
        c.roundRect(0, 0, self._width, self._height, self.radius, fill=1, stroke=1)
        c.restoreState()
        self.content.drawOn(c, self._pad, self._pad)
