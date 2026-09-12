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
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def ensure_fonts() -> tuple[str, str]:
    global FONT, FONT_BOLD
    windir = Path("C:/Windows/Fonts")
    candidates = [
        (windir / "segoeui.ttf", windir / "segoeuib.ttf"),
        (windir / "arial.ttf", windir / "arialbd.ttf"),
        (Path("assets/fonts/DejaVuSans.ttf"), Path("assets/fonts/DejaVuSans-Bold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            if "EnterpriseSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("EnterpriseSans", str(regular)))
                pdfmetrics.registerFont(TTFont("EnterpriseSans-Bold", str(bold)))
            FONT = "EnterpriseSans"
            FONT_BOLD = "EnterpriseSans-Bold"
            break
    return FONT, FONT_BOLD


def styles() -> dict[str, ParagraphStyle]:
    ensure_fonts()
    return {
        "title": ParagraphStyle(
            "PdfTitle",
            fontName=FONT_BOLD,
            fontSize=22,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=8,
            leading=26,
        ),
        "company": ParagraphStyle(
            "PdfCompany",
            fontName=FONT_BOLD,
            fontSize=11,
            textColor=NAVY,
            alignment=TA_RIGHT,
            leading=14,
        ),
        "meta": ParagraphStyle(
            "PdfMeta",
            fontName=FONT,
            fontSize=9,
            textColor=MUTED,
            alignment=TA_RIGHT,
            leading=12,
        ),
        "label": ParagraphStyle(
            "PdfLabel",
            fontName=FONT_BOLD,
            fontSize=8,
            textColor=MUTED,
            leading=11,
        ),
        "body": ParagraphStyle(
            "PdfBody",
            fontName=FONT,
            fontSize=9,
            textColor=NAVY,
            leading=12,
            alignment=TA_LEFT,
        ),
        "body_right": ParagraphStyle(
            "PdfBodyRight",
            fontName=FONT,
            fontSize=9,
            textColor=NAVY,
            leading=12,
            alignment=TA_RIGHT,
        ),
        "th": ParagraphStyle(
            "PdfTh",
            fontName=FONT_BOLD,
            fontSize=8,
            textColor=NAVY,
            alignment=TA_CENTER,
            leading=11,
        ),
        "td": ParagraphStyle(
            "PdfTd",
            fontName=FONT,
            fontSize=8,
            textColor=NAVY,
            leading=11,
        ),
        "td_right": ParagraphStyle(
            "PdfTdRight",
            fontName=FONT,
            fontSize=8,
            textColor=NAVY,
            alignment=TA_RIGHT,
            leading=11,
        ),
        "footer": ParagraphStyle(
            "PdfFooter",
            fontName=FONT,
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
        "caption": ParagraphStyle(
            "PdfCaption",
            fontName=FONT,
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=10,
        ),
    }
