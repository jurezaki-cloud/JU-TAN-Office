from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.theme.colors import LightColors

NAVY = HexColor(LightColors.TEXT)
PRIMARY = HexColor(LightColors.PRIMARY)
MUTED = HexColor(LightColors.SECONDARY)
BORDER = HexColor(LightColors.BORDER)
TABLE_HEADER = HexColor(LightColors.TABLE_HEADER)
SURFACE = HexColor(LightColors.SURFACE)
WHITE = white

PAD = 12

# Never use Helvetica for Slovenian text — it lacks č/š/ž glyphs.
_FALLBACK_FONT = "Helvetica"
_FALLBACK_BOLD = "Helvetica-Bold"
FONT = _FALLBACK_FONT
FONT_BOLD = _FALLBACK_BOLD
_FONTS_READY = False


def ensure_fonts() -> tuple[str, str]:
    """Register a Unicode TTF pair and return (regular, bold) font names.

    Callers must use the returned names (or re-read via this function). Do not
    capture module-level FONT at import time — that freezes Helvetica forever.
    """
    global FONT, FONT_BOLD, _FONTS_READY
    if _FONTS_READY and FONT != _FALLBACK_FONT:
        return FONT, FONT_BOLD

    windir = Path("C:/Windows/Fonts")
    candidates = [
        (windir / "segoeui.ttf", windir / "segoeuib.ttf"),
        (windir / "arial.ttf", windir / "arialbd.ttf"),
        (Path("assets/fonts/DejaVuSans.ttf"), Path("assets/fonts/DejaVuSans-Bold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            registered = set(pdfmetrics.getRegisteredFontNames())
            if "EnterpriseSans" not in registered:
                pdfmetrics.registerFont(TTFont("EnterpriseSans", str(regular)))
                pdfmetrics.registerFont(TTFont("EnterpriseSans-Bold", str(bold)))
            FONT = "EnterpriseSans"
            FONT_BOLD = "EnterpriseSans-Bold"
            _FONTS_READY = True
            break
    return FONT, FONT_BOLD


def styles() -> dict[str, ParagraphStyle]:
    regular, bold = ensure_fonts()
    return {
        "title": ParagraphStyle(
            "PdfTitle",
            fontName=bold,
            fontSize=22,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=8,
            leading=26,
        ),
        "company": ParagraphStyle(
            "PdfCompany",
            fontName=bold,
            fontSize=11,
            textColor=NAVY,
            alignment=TA_RIGHT,
            leading=14,
        ),
        "meta": ParagraphStyle(
            "PdfMeta",
            fontName=regular,
            fontSize=9,
            textColor=MUTED,
            alignment=TA_RIGHT,
            leading=12,
        ),
        "label": ParagraphStyle(
            "PdfLabel",
            fontName=bold,
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        "body": ParagraphStyle(
            "PdfBody",
            fontName=regular,
            fontSize=9,
            textColor=NAVY,
            leading=12,
            alignment=TA_LEFT,
        ),
        "body_right": ParagraphStyle(
            "PdfBodyRight",
            fontName=regular,
            fontSize=9,
            textColor=NAVY,
            leading=12,
            alignment=TA_RIGHT,
        ),
        "th": ParagraphStyle(
            "PdfTh",
            fontName=bold,
            fontSize=8,
            textColor=NAVY,
            alignment=TA_CENTER,
            leading=11,
        ),
        "td": ParagraphStyle(
            "PdfTd",
            fontName=regular,
            fontSize=8,
            textColor=NAVY,
            leading=11,
        ),
        "td_right": ParagraphStyle(
            "PdfTdRight",
            fontName=regular,
            fontSize=8,
            textColor=NAVY,
            alignment=TA_RIGHT,
            leading=11,
        ),
        "footer": ParagraphStyle(
            "PdfFooter",
            fontName=regular,
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
        "caption": ParagraphStyle(
            "PdfCaption",
            fontName=regular,
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
    }
