from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget

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


class SupplierToolbar(QWidget):
    new_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()
    refresh_clicked = Signal()
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SupplierToolbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči dobavitelja...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(240)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.status = QComboBox()
        self.status.setObjectName("EnterpriseFilter")
        self.status.setMinimumHeight(36)
        self.status.addItem("Vsi statusi", "all")
        self.status.addItem("Aktiven", "Active")
        self.status.addItem("Neaktiven", "Inactive")

        self.btn_new = QPushButton("Nov dobavitelj")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")
        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")

        layout.addWidget(self.search)
        layout.addWidget(self.status)
        for button in (self.btn_new, self.btn_edit, self.btn_delete, self.btn_refresh):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_new.clicked.connect(self.new_clicked.emit)
        self.btn_edit.clicked.connect(self.edit_clicked.emit)
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.status.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
