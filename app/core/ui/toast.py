"""Neblokirajoča toast obvestila (uspešna dejanja)."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class ToastBanner(QFrame):
    def __init__(self, parent: QWidget, message: str, kind: str = "success") -> None:
        super().__init__(parent)
        self.setObjectName("ToastBanner")
        self.setProperty("kind", kind)
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        label = QLabel(message)
        label.setObjectName("ToastLabel")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        self.adjustSize()

    def place(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()
        x = parent.width() - self.width() - 24
        y = 24
        self.move(max(16, x), y)
        self.raise_()


def show_toast(context: QWidget | None, message: str, kind: str = "success", ms: int = 2800) -> None:
    if not message:
        return
    host = None
    if context is not None:
        host = context.window() if hasattr(context, "window") else context
    if host is None:
        return
    banner = ToastBanner(host, message, kind)
    banner.place()
    banner.show()
    # Fade via graphics effect — never windowOpacity (promotes child to top-level).
    from PySide6.QtWidgets import QGraphicsOpacityEffect

    effect = QGraphicsOpacityEffect(banner)
    banner.setGraphicsEffect(effect)
    fade = QPropertyAnimation(effect, b"opacity", banner)
    fade.setDuration(280)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.OutCubic)
    fade.start()
    QTimer.singleShot(ms, banner.deleteLater)
