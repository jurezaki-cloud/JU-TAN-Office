from pathlib import Path

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import QPushButton, QSizePolicy

from app.theme.colors import LightColors


class NavigationButton(QPushButton):
    clicked_index = Signal(int)

    def __init__(
        self,
        text: str,
        index: int,
        icon: QIcon | str | Path | None = None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.index = index
        self._hover = 0.0

        self.setObjectName("NavigationButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.NoFocus)

        self._hover_anim = QPropertyAnimation(self, b"hoverProgress", self)
        self._hover_anim.setDuration(160)
        self._hover_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.set_navigation_icon(icon)
        self.clicked.connect(self._emit_index)

    def get_hover_progress(self) -> float:
        return self._hover

    def set_hover_progress(self, value: float) -> None:
        self._hover = float(value)
        self.update()

    hoverProgress = Property(float, get_hover_progress, set_hover_progress)

    def set_navigation_icon(self, icon: QIcon | str | Path | None) -> None:
        if icon is None:
            return

        if isinstance(icon, (str, Path)):
            path = Path(icon)
            if not path.exists():
                return
            qicon = QIcon(str(path))
        else:
            qicon = icon

        if qicon.isNull():
            return

        self.setIcon(qicon)
        self.setIconSize(QSize(18, 18))

    def enterEvent(self, event):
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _animate_hover(self, target: float) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover)
        self._hover_anim.setEndValue(target)
        self._hover_anim.start()

    def paintEvent(self, event):
        if self._hover > 0 and not self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            color = QColor(LightColors.PRIMARY)
            color.setAlphaF(0.16 * self._hover)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
            painter.end()

        super().paintEvent(event)

    def _emit_index(self):
        self.clicked_index.emit(self.index)
