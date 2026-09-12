from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.modules.automation.automation_repository import TRIGGERS
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


class AutomationToolbar(QWidget):
    new_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()
    duplicate_clicked = Signal()
    enable_clicked = Signal()
    disable_clicked = Signal()
    run_clicked = Signal()
    refresh_clicked = Signal()
    export_clicked = Signal()
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AutomationToolbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči pravila po imenu, opisu ali sprožilcu...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(220)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.trigger = QComboBox()
        self.enabled = QComboBox()
        self.log_result = QComboBox()
        for combo in (self.trigger, self.enabled, self.log_result):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)
        self.trigger.addItem("Vsi sprožilci", "all")
        for key, label in TRIGGERS:
            self.trigger.addItem(label, key)
        self.enabled.addItem("Vsa stanja", "all")
        self.enabled.addItem("Omogočeno", "on")
        self.enabled.addItem("Onemogočeno", "off")
        self.log_result.addItem("Vsi rezultati", "all")
        self.log_result.addItem("Uspeh", "success")
        self.log_result.addItem("Napaka", "failed")
        self.log_result.addItem("Preskočeno", "skipped")

        buttons = [
            ("New Rule", "PrimaryButton", "new_clicked"),
            ("Edit", "SecondaryButton", "edit_clicked"),
            ("Delete", "SecondaryButton", "delete_clicked"),
            ("Duplicate", "SecondaryButton", "duplicate_clicked"),
            ("Enable", "SecondaryButton", "enable_clicked"),
            ("Disable", "SecondaryButton", "disable_clicked"),
            ("Run Now", "SecondaryButton", "run_clicked"),
            ("Refresh", "SecondaryButton", "refresh_clicked"),
            ("Export", "SecondaryButton", "export_clicked"),
        ]
        layout.addWidget(self.search)
        layout.addWidget(self.trigger)
        layout.addWidget(self.enabled)
        layout.addWidget(self.log_result)
        for title, style, signal_name in buttons:
            button = QPushButton(title)
            button.setObjectName(style)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            button.clicked.connect(getattr(self, signal_name).emit)
            layout.addWidget(button)

        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.trigger.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.enabled.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.log_result.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
