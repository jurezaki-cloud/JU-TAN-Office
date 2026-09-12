from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QVBoxLayout,
)

from app.theme.colors import LightColors


def make_card_shadow(parent, alpha: int = 22, blur: int = 16) -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect(parent)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, 2)
    color = QColor(LightColors.TEXT)
    color.setAlpha(alpha)
    shadow.setColor(color)
    return shadow


class EnterpriseCard(QFrame):

    def __init__(self, object_name: str = "DashboardCard", parent=None):
        super().__init__(parent)

        self.setObjectName(object_name)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self._rest_blur = 16
        self._hover_blur = 28
        self._shadow = make_card_shadow(self, blur=self._rest_blur)
        self.setGraphicsEffect(self._shadow)

        self._blur_anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._blur_anim.setDuration(160)
        self._blur_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 20, 20, 20)
        self.body.setSpacing(12)

    def enterEvent(self, event):
        self._animate_blur(self._hover_blur)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_blur(self._rest_blur)
        super().leaveEvent(event)

    def _animate_blur(self, target: float) -> None:
        self._blur_anim.stop()
        self._blur_anim.setStartValue(self._shadow.blurRadius())
        self._blur_anim.setEndValue(target)
        self._blur_anim.start()
