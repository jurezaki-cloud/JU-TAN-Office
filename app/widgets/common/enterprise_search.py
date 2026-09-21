"""Shared enterprise search field for document list toolbars."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSizePolicy, QWidget

from app.theme.colors import semantic_color
from app.theme.tokens import CONTROL_HEIGHT


def _search_icon() -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(semantic_color("SECONDARY")))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawEllipse(2, 2, 10, 10)
    painter.drawLine(11, 11, 16, 16)
    painter.end()
    return QIcon(pixmap)


class EnterpriseSearchField(QWidget):
    """Leading-icon search input with clear button and stable toolbar sizing."""

    textChanged = Signal(str)

    def __init__(self, placeholder: str, *, object_name: str = "EnterpriseSearchHost", parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QLineEdit()
        self.input.setObjectName("EnterpriseSearch")
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)
        self.input.setMinimumHeight(CONTROL_HEIGHT)
        self.input.setMaximumHeight(CONTROL_HEIGHT)
        self.input.setMinimumWidth(160)
        self.input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input.addAction(_search_icon(), QLineEdit.LeadingPosition)

        layout.addWidget(self.input)
        self.input.textChanged.connect(self.textChanged.emit)

    def text(self) -> str:
        return self.input.text()

    def setText(self, text: str) -> None:
        self.input.setText(text)
