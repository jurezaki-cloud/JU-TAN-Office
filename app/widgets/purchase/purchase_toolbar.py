from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from app.theme.colors import semantic_color
from app.widgets.common.filter_controls import compact_filter
from app.widgets.common.toolbar_overflow import ToolbarOverflowButton


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


class PurchaseToolbar(QWidget):
    new_clicked = Signal()
    receive_clicked = Signal()
    print_clicked = Signal()
    pdf_clicked = Signal()
    excel_clicked = Signal()
    refresh_clicked = Signal()
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PurchaseToolbar")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči nabavo...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(140)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.supplier = QComboBox()
        self.status = QComboBox()
        self.date_mode = QComboBox()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        for combo in (self.supplier, self.status, self.date_mode):
            compact_filter(combo)
        compact_filter(self.date)
        self.date_mode.addItem("Vsi datumi", "all")
        self.date_mode.addItem("Danes", "today")
        self.date_mode.addItem("Ta mesec", "month")
        self.date_mode.addItem("Izbrani dan", "day")

        self.btn_new = QPushButton("Nova nabava")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_receive = QPushButton("Prevzem")
        self.btn_receive.setObjectName("SecondaryButton")

        self.btn_print = QPushButton("Natisni")
        self.btn_print.setObjectName("SecondaryButton")
        self.btn_pdf = QPushButton("PDF")
        self.btn_pdf.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("SecondaryButton")
        for hidden in (self.btn_print, self.btn_pdf, self.btn_excel, self.btn_refresh):
            hidden.hide()

        self.btn_more = ToolbarOverflowButton()
        self.btn_more.add_actions(
            (
                ("Natisni", self.print_clicked.emit),
                ("PDF", self.pdf_clicked.emit),
                ("Excel", self.excel_clicked.emit),
                ("Refresh", self.refresh_clicked.emit),
            )
        )

        layout.addWidget(self.search, 1)
        layout.addWidget(self.supplier)
        layout.addWidget(self.status)
        layout.addWidget(self.date_mode)
        layout.addWidget(self.date)
        for button in (self.btn_new, self.btn_receive):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)
        for button in (self.btn_print, self.btn_pdf, self.btn_excel, self.btn_refresh):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
        layout.addWidget(self.btn_more)

        self.btn_new.clicked.connect(self.new_clicked.emit)
        self.btn_receive.clicked.connect(self.receive_clicked.emit)
        self.btn_print.clicked.connect(self.print_clicked.emit)
        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.supplier.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.status.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.date_mode.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.date.dateChanged.connect(lambda _: self.filter_changed.emit())

    def fill_suppliers(self, rows: list) -> None:
        current = self.supplier.currentData()
        self.supplier.blockSignals(True)
        self.supplier.clear()
        self.supplier.addItem("Vsi dobavitelji", "all")
        for row in rows:
            self.supplier.addItem(str(row[1]), row[0])
        index = self.supplier.findData(current)
        self.supplier.setCurrentIndex(index if index >= 0 else 0)
        self.supplier.blockSignals(False)

    def fill_statuses(self, statuses: tuple[str, ...]) -> None:
        if self.status.count() > 0:
            return
        self.status.addItem("Vsi statusi", "all")
        for item in statuses:
            self.status.addItem(item, item)
