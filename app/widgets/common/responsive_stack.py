"""Stacked widget that does not inherit min size from hidden pages."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QStackedWidget, QWidget


class ResponsiveStackedWidget(QStackedWidget):
    """QStackedWidget whose preferred size follows the *current* page only.

    Default Qt behavior takes the max of every page, which lets one dense
    toolbar permanently force MainWindow wider (or taller) than the screen.

    Minimum size is intentionally unconstrained so module pages compress or
    scroll inside the workspace instead of enlarging the shell.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.currentChanged.connect(self._on_current_changed)

    def _on_current_changed(self, _index: int) -> None:
        self.updateGeometry()
        parent = self.parentWidget()
        while parent is not None:
            parent.updateGeometry()
            parent = parent.parentWidget()

    def sizeHint(self) -> QSize:
        current = self.currentWidget()
        if current is not None:
            return current.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)
