"""Professional stroke icon set — one coherent family, theme-aware, HiDPI-safe.

Icons are drawn with QPainter (vector-like) so they stay sharp at any DPI
and work in both light and dark themes without external assets.
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _pen(color: QColor, width: float = 1.7) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _draw_dashboard(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3.5, 3.5, 7, 7), 1.2, 1.2)
    p.drawRoundedRect(QRectF(13.5, 3.5, 7, 7), 1.2, 1.2)
    p.drawRoundedRect(QRectF(3.5, 13.5, 7, 7), 1.2, 1.2)
    p.drawRoundedRect(QRectF(13.5, 13.5, 7, 7), 1.2, 1.2)


def _draw_invoice(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5.5, 2.5, 13, 19), 1.5, 1.5)
    p.drawLine(QPointF(8.5, 7), QPointF(15.5, 7))
    p.drawLine(QPointF(8.5, 11), QPointF(15.5, 11))
    p.drawLine(QPointF(8.5, 15), QPointF(13, 15))


def _draw_offer(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5, 2.5, 14, 19), 1.5, 1.5)
    p.drawLine(QPointF(8, 8), QPointF(16, 8))
    p.drawLine(QPointF(8, 12), QPointF(16, 12))
    p.drawLine(QPointF(8, 16), QPointF(13, 16))


def _draw_order(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5, 3, 14, 18), 1.5, 1.5)
    p.drawLine(QPointF(8, 1.5), QPointF(8, 5.5))
    p.drawLine(QPointF(16, 1.5), QPointF(16, 5.5))
    p.drawLine(QPointF(8.5, 10), QPointF(15.5, 10))
    p.drawLine(QPointF(8.5, 14), QPointF(15.5, 14))


def _draw_customers(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(9, 8), 3.2, 3.2)
    p.drawArc(QRectF(3.5, 12.5, 11, 8), 20 * 16, 140 * 16)
    p.drawEllipse(QPointF(16.5, 9.5), 2.4, 2.4)
    p.drawArc(QRectF(12, 13.5, 9, 7), 20 * 16, 120 * 16)


def _draw_articles(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 6, 16, 13), 1.5, 1.5)
    p.drawLine(QPointF(4, 11), QPointF(20, 11))
    p.drawLine(QPointF(12, 6), QPointF(12, 19))


def _draw_warehouse(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3.5, 9, 7, 10), 1, 1)
    p.drawRoundedRect(QRectF(13.5, 9, 7, 10), 1, 1)
    p.drawRoundedRect(QRectF(8.5, 3.5, 7, 10), 1, 1)


def _draw_suppliers(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(2.5, 10, 11, 7), 1, 1)
    p.drawLine(QPointF(13.5, 12), QPointF(17.5, 12))
    p.drawLine(QPointF(17.5, 12), QPointF(19.5, 15))
    p.drawLine(QPointF(19.5, 15), QPointF(19.5, 17))
    p.drawLine(QPointF(13.5, 17), QPointF(19.5, 17))
    p.drawEllipse(QPointF(6.5, 18.5), 2, 2)
    p.drawEllipse(QPointF(16.5, 18.5), 2, 2)


def _draw_purchase(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(8, 19), 1.8, 1.8)
    p.drawEllipse(QPointF(17, 19), 1.8, 1.8)
    p.drawLine(QPointF(3, 4), QPointF(6, 4))
    p.drawLine(QPointF(6, 4), QPointF(8, 14))
    p.drawLine(QPointF(8, 14), QPointF(18.5, 14))
    p.drawLine(QPointF(18.5, 14), QPointF(20, 7))
    p.drawLine(QPointF(7.5, 10), QPointF(17.5, 10))


def _draw_payments(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 6, 18, 12), 2, 2)
    p.drawLine(QPointF(3, 10.5), QPointF(21, 10.5))
    p.drawLine(QPointF(7, 14.5), QPointF(11, 14.5))


def _draw_analytics(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawLine(QPointF(4, 18), QPointF(4, 6))
    p.drawLine(QPointF(4, 18), QPointF(20, 18))
    p.drawPolyline(
        [
            QPointF(6, 14),
            QPointF(10, 10),
            QPointF(13, 12.5),
            QPointF(18, 6.5),
        ]
    )


def _draw_reports(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5, 2.5, 14, 19), 1.5, 1.5)
    p.drawLine(QPointF(8, 8), QPointF(8, 16))
    p.drawLine(QPointF(12, 11), QPointF(12, 16))
    p.drawLine(QPointF(16, 7), QPointF(16, 16))


def _draw_documents(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 6, 16, 13), 1.2, 1.2)
    p.drawLine(QPointF(8, 6), QPointF(8, 3.5))
    p.drawLine(QPointF(8, 3.5), QPointF(14, 3.5))
    p.drawLine(QPointF(14, 3.5), QPointF(14, 6))


def _draw_crm(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(8.5, 8), 3, 3)
    p.drawEllipse(QPointF(15.5, 8), 3, 3)
    p.drawArc(QRectF(3.5, 12, 10, 8), 20 * 16, 140 * 16)
    p.drawArc(QRectF(10.5, 12, 10, 8), 20 * 16, 140 * 16)


def _draw_travel(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(3, 10, 18, 7), 1.5, 1.5)
    p.drawLine(QPointF(6, 10), QPointF(8, 6))
    p.drawLine(QPointF(8, 6), QPointF(15, 6))
    p.drawLine(QPointF(15, 6), QPointF(17.5, 10))
    p.drawEllipse(QPointF(7.5, 17.5), 2, 2)
    p.drawEllipse(QPointF(16.5, 17.5), 2, 2)


def _draw_automation(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(7, 7), 2.5, 2.5)
    p.drawEllipse(QPointF(17, 7), 2.5, 2.5)
    p.drawEllipse(QPointF(12, 17), 2.5, 2.5)
    p.drawLine(QPointF(9.2, 8.2), QPointF(14.8, 8.2))
    p.drawLine(QPointF(8.2, 9.2), QPointF(10.8, 15))
    p.drawLine(QPointF(15.8, 9.2), QPointF(13.2, 15))


def _draw_company(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRect(QRectF(4.5, 5, 15, 15))
    p.drawLine(QPointF(4.5, 9), QPointF(19.5, 9))
    p.drawLine(QPointF(4.5, 13.5), QPointF(19.5, 13.5))
    p.drawLine(QPointF(9.5, 9), QPointF(9.5, 20))
    p.drawLine(QPointF(14.5, 9), QPointF(14.5, 20))


def _draw_settings(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 12), 3.2, 3.2)
    for angle in range(0, 360, 45):
        from math import cos, radians, sin

        a = radians(angle)
        p.drawLine(
            QPointF(12 + cos(a) * 5.2, 12 + sin(a) * 5.2),
            QPointF(12 + cos(a) * 8.2, 12 + sin(a) * 8.2),
        )


def _draw_new(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c, 2.0))
    p.drawLine(QPointF(12, 5), QPointF(12, 19))
    p.drawLine(QPointF(5, 12), QPointF(19, 12))


def _draw_search(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(10, 10), 5, 5)
    p.drawLine(QPointF(13.8, 13.8), QPointF(19, 19))


def _draw_save(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 3.5, 16, 17), 1.5, 1.5)
    p.drawRect(QRectF(8, 3.5, 8, 5))
    p.drawRect(QRectF(7.5, 12, 9, 6))


def _draw_edit(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawLine(QPointF(13.5, 5), QPointF(19, 10.5))
    p.drawLine(QPointF(5, 13.5), QPointF(12.5, 6))
    p.drawLine(QPointF(5, 13.5), QPointF(5, 19))
    p.drawLine(QPointF(5, 19), QPointF(10.5, 19))


def _draw_delete(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawLine(QPointF(5, 7), QPointF(19, 7))
    p.drawLine(QPointF(9, 4.5), QPointF(15, 4.5))
    p.drawRoundedRect(QRectF(6.5, 7, 11, 13), 1.2, 1.2)
    p.drawLine(QPointF(10, 10), QPointF(10, 16))
    p.drawLine(QPointF(14, 10), QPointF(14, 16))


def _draw_pdf(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(5, 2.5, 14, 19), 1.5, 1.5)
    p.drawLine(QPointF(8, 9), QPointF(16, 9))
    p.drawLine(QPointF(8, 13), QPointF(14, 13))


def _draw_print(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(6, 3, 12, 6), 1, 1)
    p.drawRoundedRect(QRectF(3.5, 8, 17, 9), 1.5, 1.5)
    p.drawRoundedRect(QRectF(7, 14, 10, 6), 1, 1)


def _draw_export(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawLine(QPointF(12, 4), QPointF(12, 14))
    p.drawLine(QPointF(8, 8), QPointF(12, 4))
    p.drawLine(QPointF(16, 8), QPointF(12, 4))
    p.drawRoundedRect(QRectF(5, 14, 14, 6), 1.2, 1.2)


def _draw_refresh(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawArc(QRectF(4.5, 4.5, 15, 15), 40 * 16, 240 * 16)
    p.drawLine(QPointF(16.5, 4.5), QPointF(19.5, 7.5))
    p.drawLine(QPointF(16.5, 4.5), QPointF(13.5, 7.5))


def _draw_lock(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(6, 11, 12, 9), 1.5, 1.5)
    p.drawArc(QRectF(8, 4.5, 8, 9), 0, 180 * 16)


def _draw_filter(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawLine(QPointF(4, 6), QPointF(20, 6))
    p.drawLine(QPointF(7, 12), QPointF(17, 12))
    p.drawLine(QPointF(10, 18), QPointF(14, 18))


def _draw_calendar(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawRoundedRect(QRectF(4, 5, 16, 15), 1.5, 1.5)
    p.drawLine(QPointF(4, 10), QPointF(20, 10))
    p.drawLine(QPointF(9, 3), QPointF(9, 7))
    p.drawLine(QPointF(15, 3), QPointF(15, 7))


def _draw_more(p: QPainter, c: QColor) -> None:
    p.setBrush(c)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(6, 12), 1.6, 1.6)
    p.drawEllipse(QPointF(12, 12), 1.6, 1.6)
    p.drawEllipse(QPointF(18, 12), 1.6, 1.6)


def _draw_user(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c))
    p.drawEllipse(QPointF(12, 8), 3.5, 3.5)
    p.drawArc(QRectF(5.5, 13, 13, 9), 20 * 16, 140 * 16)


def _draw_collapse(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c, 1.9))
    p.drawLine(QPointF(14, 6), QPointF(8, 12))
    p.drawLine(QPointF(8, 12), QPointF(14, 18))


def _draw_expand(p: QPainter, c: QColor) -> None:
    p.setPen(_pen(c, 1.9))
    p.drawLine(QPointF(10, 6), QPointF(16, 12))
    p.drawLine(QPointF(16, 12), QPointF(10, 18))


_DRAWERS = {
    "dashboard": _draw_dashboard,
    "invoices": _draw_invoice,
    "offers": _draw_offer,
    "orders": _draw_order,
    "customers": _draw_customers,
    "articles": _draw_articles,
    "warehouse": _draw_warehouse,
    "suppliers": _draw_suppliers,
    "purchase": _draw_purchase,
    "payments": _draw_payments,
    "analytics": _draw_analytics,
    "reports": _draw_reports,
    "documents": _draw_documents,
    "crm": _draw_crm,
    "travel": _draw_travel,
    "automation": _draw_automation,
    "company": _draw_company,
    "settings": _draw_settings,
    "new": _draw_new,
    "search": _draw_search,
    "save": _draw_save,
    "edit": _draw_edit,
    "delete": _draw_delete,
    "pdf": _draw_pdf,
    "print": _draw_print,
    "export": _draw_export,
    "refresh": _draw_refresh,
    "lock": _draw_lock,
    "filter": _draw_filter,
    "calendar": _draw_calendar,
    "more": _draw_more,
    "user": _draw_user,
    "collapse": _draw_collapse,
    "expand": _draw_expand,
}

# Navigation page index → icon key
NAV_ICONS: dict[int, str] = {
    0: "dashboard",
    1: "invoices",
    2: "customers",
    3: "offers",
    4: "articles",
    5: "company",
    6: "payments",
    7: "analytics",
    8: "settings",
    9: "orders",
    10: "warehouse",
    11: "suppliers",
    12: "purchase",
    13: "documents",
    14: "crm",
    15: "reports",
    16: "automation",
    17: "travel",
}


@lru_cache(maxsize=256)
def _pixmap(name: str, color_hex: str, size: int, dpr: int) -> QPixmap:
    drawer = _DRAWERS.get(name)
    if drawer is None:
        return QPixmap()
    px = max(16, int(size * dpr))
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    scale = px / 24.0
    painter.scale(scale, scale)
    drawer(painter, QColor(color_hex))
    painter.end()
    pm.setDevicePixelRatio(float(dpr))
    return pm


def brand_icon(
    name: str,
    *,
    color: str | None = None,
    size: int = 18,
    dpr: float = 1.0,
) -> QIcon:
    """Return a cached theme-aware stroke icon."""
    if color is None:
        from app.theme.colors import semantic_color

        color = semantic_color("SIDEBAR_TEXT", "#F8FAFC")
    dpr_i = max(1, int(round(dpr)))
    pm = _pixmap(name, color, size, dpr_i)
    if pm.isNull():
        return QIcon()
    icon = QIcon()
    icon.addPixmap(pm)
    return icon


def clear_icon_cache() -> None:
    _pixmap.cache_clear()
