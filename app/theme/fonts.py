from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


FONT_FAMILY = "Segoe UI"
FONT_SIZE_PT = 10
FONT_SIZE_PX = "13px"
FONT_TITLE_PX = "24px"
FONT_TITLE_LARGE_PX = "28px"
FONT_SECTION_PX = "18px"
FONT_STAT_VALUE_PX = "30px"


_FONT_CACHE: dict[int, QFont] = {}


def build_application_font(point_size: int | None = None) -> QFont:
    size = point_size or FONT_SIZE_PT
    hit = _FONT_CACHE.get(size)
    if hit is not None:
        return QFont(hit)
    font = QFont(FONT_FAMILY)
    font.setPointSize(size)
    _FONT_CACHE[size] = QFont(font)
    return font


def apply_fonts(app: QApplication, point_size: int | None = None) -> None:
    app.setFont(build_application_font(point_size))
