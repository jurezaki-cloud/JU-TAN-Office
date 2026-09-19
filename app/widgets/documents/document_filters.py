from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)

from app.theme.colors import semantic_color
from app.widgets.common.filter_controls import compact_filter


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


class DocumentFilters(QWidget):
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentFilters")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.path = QLabel("Dokumenti")
        self.path.setObjectName("KpiHint")
        self.path.setMinimumWidth(0)
        self.path.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči dokument...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(120)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.kind = QComboBox()
        self.module = QComboBox()
        self.owner = QComboBox()
        self.date_mode = QComboBox()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        for combo in (self.kind, self.module, self.owner, self.date_mode):
            compact_filter(combo)
        compact_filter(self.date)

        self.kind.addItem("Vsi tipi", "all")
        self.kind.addItem("PDF", "pdf")
        self.kind.addItem("Slike", "image")
        self.kind.addItem("Word", "docx")
        self.kind.addItem("Excel", "xlsx")
        self.kind.addItem("ZIP", "zip")
        self.kind.addItem("TXT", "txt")

        self.date_mode.addItem("Vsi datumi", "all")
        self.date_mode.addItem("Danes", "today")
        self.date_mode.addItem("Ta mesec", "month")
        self.date_mode.addItem("Izbrani dan", "day")

        layout.addWidget(self.path)
        layout.addWidget(self.search, 1)
        layout.addWidget(self.kind)
        layout.addWidget(self.module)
        layout.addWidget(self.date_mode)
        layout.addWidget(self.date)
        layout.addWidget(self.owner)

        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.kind.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.module.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.owner.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.date_mode.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.date.dateChanged.connect(lambda _: self.filter_changed.emit())

    def fill_modules(self, items: tuple[tuple[str, str], ...]) -> None:
        if self.module.count():
            return
        self.module.addItem("Vsi moduli", "all")
        for key, label in items:
            self.module.addItem(label, key)

    def fill_owners(self, owners: list[str]) -> None:
        current = self.owner.currentData()
        self.owner.blockSignals(True)
        self.owner.clear()
        self.owner.addItem("Vsi lastniki", "all")
        for owner in owners:
            self.owner.addItem(owner, owner)
        index = self.owner.findData(current)
        self.owner.setCurrentIndex(index if index >= 0 else 0)
        self.owner.blockSignals(False)
