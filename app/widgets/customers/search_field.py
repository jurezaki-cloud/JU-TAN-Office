from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget

from app.theme.colors import semantic_color


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


class CustomerSearch(QWidget):
    textChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("CustomerSearch")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QLineEdit()
        self.input.setObjectName("EnterpriseSearch")
        self.input.setPlaceholderText("Išči stranko po podjetju, kontaktu ali mestu...")
        self.input.setClearButtonEnabled(True)
        self.input.setMinimumHeight(36)
        self.input.addAction(_search_icon(), QLineEdit.LeadingPosition)
        self.input.setMinimumWidth(160)

        layout.addWidget(self.input)
        self.input.textChanged.connect(self.textChanged.emit)

    def text(self) -> str:
        return self.input.text()

    def setText(self, text: str) -> None:
        self.input.setText(text)
