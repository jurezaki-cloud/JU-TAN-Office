"""Typography and ParagraphStyles for commercial PDFs."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.pdf.pdf_branding import resolve_palette
from app.theme.colors import LightColors

# Module-level defaults — used when callers do not pass branded options.
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
        # Use the same font family on every supported OS whenever possible.
        # Stable font metrics prevent one-page PDFs from reflowing in Linux CI.
        (Path("assets/fonts/DejaVuSans.ttf"), Path("assets/fonts/DejaVuSans-Bold.ttf")),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (windir / "DejaVuSans.ttf", windir / "DejaVuSans-Bold.ttf"),
        # Last-resort Windows fallbacks for machines without DejaVu.
        (windir / "segoeui.ttf", windir / "segoeuib.ttf"),
        (windir / "calibri.ttf", windir / "calibrib.ttf"),
        (windir / "arial.ttf", windir / "arialbd.ttf"),
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


def styles(options: dict | None = None) -> dict[str, ParagraphStyle]:
    regular, bold = ensure_fonts()
    palette = resolve_palette(options)
    navy = palette["text"]
    muted = palette["muted"]
    accent = palette["primary"]
    return {
        "title": ParagraphStyle(
            "PdfTitle",
            fontName=bold,
            fontSize=32,
            textColor=navy,
            alignment=TA_RIGHT,
            spaceAfter=0,
            leading=36,
        ),
        "doc_number": ParagraphStyle(
            "PdfDocNumber",
            fontName=bold,
            fontSize=14.8,
            textColor=accent,
            alignment=TA_RIGHT,
            leading=17.5,
        ),
        "company": ParagraphStyle(
            "PdfCompany",
            fontName=bold,
            fontSize=12.6,
            textColor=navy,
            alignment=TA_RIGHT,
            leading=15.0,
        ),
        "meta": ParagraphStyle(
            "PdfMeta",
            fontName=regular,
            fontSize=10.0,
            textColor=muted,
            alignment=TA_RIGHT,
            leading=12.2,
        ),
        "meta_contact": ParagraphStyle(
            "PdfMetaContact",
            fontName=regular,
            fontSize=10.0,
            textColor=muted,
            alignment=TA_RIGHT,
            leading=12.2,
        ),
        "meta_label": ParagraphStyle(
            "PdfMetaLabel",
            fontName=bold,
            fontSize=11.5,
            textColor=navy,
            alignment=TA_LEFT,
            leading=14.2,
        ),
        "meta_value": ParagraphStyle(
            "PdfMetaValue",
            fontName=regular,
            fontSize=11.5,
            textColor=navy,
            alignment=TA_RIGHT,
            leading=14.2,
        ),
        "logo_tagline": ParagraphStyle(
            "PdfLogoTagline",
            fontName=regular,
            fontSize=7.8,
            textColor=muted,
            alignment=TA_CENTER,
            leading=9.4,
        ),
        "label": ParagraphStyle(
            "PdfLabel",
            fontName=bold,
            fontSize=11.2,
            textColor=accent,
            leading=14.2,
        ),
        "section": ParagraphStyle(
            "PdfSection",
            fontName=bold,
            fontSize=13.0,
            textColor=accent,
            leading=16.0,
        ),
        "body": ParagraphStyle(
            "PdfBody",
            fontName=regular,
            fontSize=10.8,
            textColor=navy,
            leading=13.5,
            alignment=TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "PdfBodyBold",
            fontName=bold,
            fontSize=12.0,
            textColor=navy,
            leading=14.6,
            alignment=TA_LEFT,
        ),
        "body_right": ParagraphStyle(
            "PdfBodyRight",
            fontName=regular,
            fontSize=10.8,
            textColor=navy,
            leading=13.8,
            alignment=TA_RIGHT,
        ),
        "th": ParagraphStyle(
            "PdfTh",
            fontName=bold,
            fontSize=11.0,
            textColor=white,
            alignment=TA_LEFT,
            leading=14.5,
        ),
        "th_right": ParagraphStyle(
            "PdfThRight",
            fontName=bold,
            fontSize=11.0,
            textColor=white,
            alignment=TA_RIGHT,
            leading=14.5,
        ),
        "td": ParagraphStyle(
            "PdfTd",
            fontName=regular,
            fontSize=11.5,
            textColor=navy,
            leading=14.8,
        ),
        "td_right": ParagraphStyle(
            "PdfTdRight",
            fontName=regular,
            fontSize=11.5,
            textColor=navy,
            alignment=TA_RIGHT,
            leading=14.8,
        ),
        "footer": ParagraphStyle(
            "PdfFooter",
            fontName=regular,
            fontSize=9,
            textColor=muted,
            alignment=TA_CENTER,
            leading=11,
        ),
        "caption": ParagraphStyle(
            "PdfCaption",
            fontName=regular,
            fontSize=9.2,
            textColor=muted,
            alignment=TA_CENTER,
            leading=11.5,
        ),
        "sign_name": ParagraphStyle(
            "PdfSignName",
            fontName=bold,
            fontSize=9,
            textColor=navy,
            alignment=TA_CENTER,
            leading=11,
        ),
        "sign_role": ParagraphStyle(
            "PdfSignRole",
            fontName=regular,
            fontSize=8.5,
            textColor=muted,
            alignment=TA_CENTER,
            leading=10,
        ),
        "total_label": ParagraphStyle(
            "PdfTotalLabel",
            fontName=bold,
            fontSize=11.0,
            textColor=navy,
            leading=14.0,
            alignment=TA_LEFT,
        ),
        "total_value": ParagraphStyle(
            "PdfTotalValue",
            fontName=regular,
            fontSize=11.0,
            textColor=navy,
            alignment=TA_RIGHT,
            leading=14.0,
        ),
        "pay_label": ParagraphStyle(
            "PdfPayLabel",
            fontName=bold,
            fontSize=12.2,
            textColor=white,
            leading=15.2,
        ),
        "pay_value": ParagraphStyle(
            "PdfPayValue",
            fontName=bold,
            fontSize=14.5,
            textColor=white,
            alignment=TA_RIGHT,
            leading=17.0,
        ),
        "thanks": ParagraphStyle(
            "PdfThanks",
            fontName=bold,
            fontSize=17.8,
            textColor=navy,
            leading=21.0,
        ),
        "thanks_sub": ParagraphStyle(
            "PdfThanksSub",
            fontName=regular,
            fontSize=10.4,
            textColor=muted,
            leading=12.8,
        ),
        "brand_tag": ParagraphStyle(
            "PdfBrandTag",
            fontName=regular,
            fontSize=9.2,
            textColor=muted,
            alignment=TA_RIGHT,
            leading=11.5,
        ),
        "brand_web": ParagraphStyle(
            "PdfBrandWeb",
            fontName=bold,
            fontSize=11.5,
            textColor=accent,
            alignment=TA_RIGHT,
            leading=14.0,
        ),
        "art94": ParagraphStyle(
            "PdfArt94",
            fontName=regular,
            fontSize=9.5,
            textColor=muted,
            leading=12.0,
            alignment=TA_LEFT,
        ),
    }
