from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QStyledItemDelegate

from app.theme.colors import semantic_color


def invoice_badge(raw_status, due_date=None) -> str:
    status = (raw_status or "").strip()

    if status in ("Plačan", "Plačano"):
        return "Plačano"
    if status in ("Delno plačan", "Delno plačano"):
        return "Delno plačano"
    if status == "Storniran":
        return "Stornirano"
    if status == "Osnutek":
        return "Osnutek"

    if due_date and status not in ("Plačan", "Plačano", "Storniran", "Delno plačan", "Delno plačano"):
        try:
            due = date.fromisoformat(str(due_date)[:10])
            if due < date.today():
                return "Zapadlo"
        except ValueError:
            pass

    if status == "Izdan":
        return "Neplačano"

    return status or "Osnutek"


def _badge_map() -> dict[str, str]:
    return {
        "Plačano": semantic_color("SUCCESS"),
        "Delno plačano": semantic_color("WARNING"),
        "Neplačano": semantic_color("WARNING"),
        "Zapadlo": semantic_color("DANGER"),
        "Osnutek": semantic_color("SECONDARY"),
        "Odobren": semantic_color("PRIMARY"),
        "Zaključen": semantic_color("SUCCESS"),
        "Storniran": semantic_color("SECONDARY"),
        "Stornirano": semantic_color("SECONDARY"),
        "Poslana": semantic_color("PRIMARY"),
        "Sprejeta": semantic_color("SUCCESS"),
        "Zavrnjena": semantic_color("DANGER"),
        "Potekla": semantic_color("DANGER"),
        "22 %": semantic_color("PRIMARY"),
        "9.5 %": semantic_color("WARNING"),
        "5 %": semantic_color("SUCCESS"),
        "0 %": semantic_color("SECONDARY"),
        "Potrjeno": semantic_color("PRIMARY"),
        "V obdelavi": semantic_color("WARNING"),
        "Dobavljeno": semantic_color("SUCCESS"),
        "Preklicano": semantic_color("DANGER"),
        "🟢 Na zalogi": semantic_color("SUCCESS"),
        "🟡 Nizka zaloga": semantic_color("WARNING"),
        "🔴 Ni zaloge": semantic_color("DANGER"),
        "Na zalogi": semantic_color("SUCCESS"),
        "Nizka zaloga": semantic_color("WARNING"),
        "Ni zaloge": semantic_color("DANGER"),
        "Izdan": semantic_color("WARNING"),
        "Prevzem": semantic_color("SUCCESS"),
        "Izdaja": semantic_color("DANGER"),
        "Korekcija": semantic_color("WARNING"),
        "Inventura": semantic_color("PRIMARY"),
        "Rezervacija": semantic_color("SECONDARY"),
        "Active": semantic_color("SUCCESS"),
        "Inactive": semantic_color("SECONDARY"),
        "Draft": semantic_color("SECONDARY"),
        "Ordered": semantic_color("PRIMARY"),
        "Partially Received": semantic_color("WARNING"),
        "Received": semantic_color("SUCCESS"),
        "Cancelled": semantic_color("DANGER"),
        "PDF": semantic_color("DANGER"),
        "PNG": semantic_color("SUCCESS"),
        "JPG": semantic_color("SUCCESS"),
        "DOCX": semantic_color("PRIMARY"),
        "XLSX": semantic_color("SUCCESS"),
        "ZIP": semantic_color("WARNING"),
        "TXT": semantic_color("SECONDARY"),
        "Mapa": semantic_color("PRIMARY"),
        "Lead": semantic_color("SECONDARY"),
        "Qualified": semantic_color("PRIMARY"),
        "Proposal": semantic_color("WARNING"),
        "Negotiation": semantic_color("WARNING"),
        "Won": semantic_color("SUCCESS"),
        "Lost": semantic_color("DANGER"),
        "High": semantic_color("DANGER"),
        "Urgent": semantic_color("DANGER"),
        "Normal": semantic_color("PRIMARY"),
        "Low": semantic_color("SECONDARY"),
    }


class _BadgeColorsProxy(dict):
    def get(self, key, default=None):  # type: ignore[override]
        return _badge_map().get(
            key,
            default if default is not None else semantic_color("SECONDARY"),
        )

    def __getitem__(self, key):
        return _badge_map()[key]

    def __contains__(self, key):
        return key in _badge_map()


BADGE_COLORS = _BadgeColorsProxy()


class StatusBadgeDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole) or ""
        color = QColor(BADGE_COLORS.get(str(text), semantic_color("SECONDARY")))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        rect = option.rect.adjusted(10, 11, -10, -11)
        if rect.width() < 36 or rect.height() < 16:
            rect = option.rect.adjusted(6, 10, -6, -10)

        fill = QColor(color)
        fill.setAlpha(28)
        border = QColor(color)
        border.setAlpha(110)

        painter.setPen(border)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 999, 999)

        painter.setPen(color)
        # QSS uses pixel fonts (pointSize == -1). Never call setPointSize with
        # that sentinel — paint with an explicit pixel size instead.
        font = QFont(option.font)
        px = font.pixelSize()
        font.setPixelSize(10 if px <= 0 else min(px, 11))
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(text))
        painter.restore()

    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        hint.setHeight(48)
        return hint
