from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QStyledItemDelegate

from app.theme.colors import LightColors


def invoice_badge(raw_status, due_date=None) -> str:
    status = (raw_status or "").strip()

    if status in ("Plačan", "Plačano"):
        return "Plačano"
    if status == "Storniran":
        return "Stornirano"
    if status == "Osnutek":
        return "Osnutek"

    if due_date and status not in ("Plačan", "Plačano", "Storniran"):
        try:
            due = date.fromisoformat(str(due_date)[:10])
            if due < date.today():
                return "Zapadlo"
        except ValueError:
            pass

    if status == "Izdan":
        return "Neplačano"

    return status or "Osnutek"


BADGE_COLORS = {
    "Plačano": LightColors.SUCCESS,
    "Neplačano": LightColors.WARNING,
    "Zapadlo": LightColors.DANGER,
    "Osnutek": LightColors.SECONDARY,
    "Stornirano": LightColors.SECONDARY,
    "Poslana": LightColors.PRIMARY,
    "Sprejeta": LightColors.SUCCESS,
    "Zavrnjena": LightColors.DANGER,
    "Potekla": LightColors.DANGER,
    "22 %": LightColors.PRIMARY,
    "9.5 %": LightColors.WARNING,
    "5 %": LightColors.SUCCESS,
    "0 %": LightColors.SECONDARY,
    "Potrjeno": LightColors.PRIMARY,
    "V obdelavi": LightColors.WARNING,
    "Dobavljeno": LightColors.SUCCESS,
    "Preklicano": LightColors.DANGER,
    "🟢 Na zalogi": LightColors.SUCCESS,
    "🟡 Nizka zaloga": LightColors.WARNING,
    "🔴 Ni zaloge": LightColors.DANGER,
    "Prevzem": LightColors.SUCCESS,
    "Izdaja": LightColors.DANGER,
    "Korekcija": LightColors.WARNING,
    "Inventura": LightColors.PRIMARY,
    "Rezervacija": LightColors.SECONDARY,
    "Active": LightColors.SUCCESS,
    "Inactive": LightColors.SECONDARY,
    "Draft": LightColors.SECONDARY,
    "Ordered": LightColors.PRIMARY,
    "Partially Received": LightColors.WARNING,
    "Received": LightColors.SUCCESS,
    "Cancelled": LightColors.DANGER,
    "PDF": LightColors.DANGER,
    "PNG": LightColors.SUCCESS,
    "JPG": LightColors.SUCCESS,
    "DOCX": LightColors.PRIMARY,
    "XLSX": LightColors.SUCCESS,
    "ZIP": LightColors.WARNING,
    "TXT": LightColors.SECONDARY,
    "Mapa": LightColors.PRIMARY,
    "Lead": LightColors.SECONDARY,
    "Qualified": LightColors.PRIMARY,
    "Proposal": LightColors.WARNING,
    "Negotiation": LightColors.WARNING,
    "Won": LightColors.SUCCESS,
    "Lost": LightColors.DANGER,
    "High": LightColors.DANGER,
    "Urgent": LightColors.DANGER,
    "Normal": LightColors.PRIMARY,
    "Low": LightColors.SECONDARY,
}


class StatusBadgeDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole) or ""
        color = QColor(BADGE_COLORS.get(str(text), LightColors.SECONDARY))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        rect = option.rect.adjusted(8, 10, -8, -10)
        fill = QColor(color)
        fill.setAlpha(28)
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, 8, 8)

        painter.setPen(color)
        font = QFont(option.font)
        font.setPointSize(9)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(text))
        painter.restore()

    def sizeHint(self, option, index):
        hint = super().sizeHint(option, index)
        hint.setHeight(48)
        return hint
