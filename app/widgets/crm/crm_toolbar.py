from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QDateEdit, QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.theme.colors import LightColors


def _search_icon() -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(LightColors.SECONDARY))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawEllipse(2, 2, 10, 10)
    painter.drawLine(11, 11, 16, 16)
    painter.end()
    return QIcon(pixmap)


class CrmToolbar(QWidget):
    lead_clicked = Signal()
    activity_clicked = Signal()
    meeting_clicked = Signal()
    refresh_clicked = Signal()
    export_clicked = Signal()
    print_clicked = Signal()
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CrmToolbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči podjetje, kontakt, email, telefon, DDV...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(220)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.salesperson = QComboBox()
        self.status = QComboBox()
        self.stage = QComboBox()
        self.priority = QComboBox()
        self.date_mode = QComboBox()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setObjectName("EnterpriseFilter")
        self.date.setMinimumHeight(36)
        for combo in (self.salesperson, self.status, self.stage, self.priority, self.date_mode):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)

        self.date_mode.addItem("Vsi datumi", "all")
        self.date_mode.addItem("Danes", "today")
        self.date_mode.addItem("Ta mesec", "month")
        self.date_mode.addItem("Izbrani dan", "day")

        self.btn_lead = QPushButton("New Lead")
        self.btn_lead.setObjectName("PrimaryButton")
        self.btn_activity = QPushButton("New Activity")
        self.btn_activity.setObjectName("SecondaryButton")
        self.btn_meeting = QPushButton("New Meeting")
        self.btn_meeting.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_export = QPushButton("Export")
        self.btn_export.setObjectName("SecondaryButton")
        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("SecondaryButton")

        layout.addWidget(self.search)
        layout.addWidget(self.salesperson)
        layout.addWidget(self.status)
        layout.addWidget(self.date_mode)
        layout.addWidget(self.date)
        layout.addWidget(self.stage)
        layout.addWidget(self.priority)
        for button in (
            self.btn_lead,
            self.btn_activity,
            self.btn_meeting,
            self.btn_refresh,
            self.btn_export,
            self.btn_print,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_lead.clicked.connect(self.lead_clicked.emit)
        self.btn_activity.clicked.connect(self.activity_clicked.emit)
        self.btn_meeting.clicked.connect(self.meeting_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_export.clicked.connect(self.export_clicked.emit)
        self.btn_print.clicked.connect(self.print_clicked.emit)
        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        for combo in (self.salesperson, self.status, self.stage, self.priority, self.date_mode):
            combo.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.date.dateChanged.connect(lambda _: self.filter_changed.emit())

    def fill(self, salespeople: list[str], statuses: tuple[str, ...], stages: tuple[str, ...], priorities: tuple[str, ...]) -> None:
        self._refill(self.salesperson, [("all", "Vsi skrbniki")] + [(item, item) for item in salespeople])
        if self.status.count() == 0:
            self.status.addItem("Vsi statusi", "all")
            for item in statuses:
                self.status.addItem(item, item)
        if self.stage.count() == 0:
            self.stage.addItem("Vsi stage", "all")
            for item in stages:
                self.stage.addItem(item, item)
        if self.priority.count() == 0:
            self.priority.addItem("Vse prioritete", "all")
            for item in priorities:
                self.priority.addItem(item, item)

    @staticmethod
    def _refill(combo: QComboBox, items: list[tuple[str, str]]) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for key, label in items:
            combo.addItem(label, key)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
