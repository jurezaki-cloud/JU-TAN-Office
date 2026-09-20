from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.modules.automation.automation_repository import TRIGGERS
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        filters = QHBoxLayout()
        filters.setContentsMargins(0, 0, 0, 0)
        filters.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči pravila po imenu, opisu ali sprožilcu...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(140)
        self.search.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.trigger = QComboBox()
        self.enabled = QComboBox()
        self.log_result = QComboBox()
        for combo in (self.trigger, self.enabled, self.log_result):
            compact_filter(combo)
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

        filters.addWidget(self.search, 1)
        filters.addWidget(self.trigger)
        filters.addWidget(self.enabled)
        filters.addWidget(self.log_result)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)

        self.btn_new = QPushButton("Novo pravilo")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")
        self.btn_run = QPushButton("Zaženi")
        self.btn_run.setObjectName("SecondaryButton")

        self.btn_delete = QPushButton("Izbriši")
        self.btn_delete.setObjectName("SecondaryButton")
        self.btn_duplicate = QPushButton("Podvoji")
        self.btn_duplicate.setObjectName("SecondaryButton")
        self.btn_enable = QPushButton("Omogoči")
        self.btn_enable.setObjectName("SecondaryButton")
        self.btn_disable = QPushButton("Onemogoči")
        self.btn_disable.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_export = QPushButton("Izvoz")
        self.btn_export.setObjectName("SecondaryButton")
        for hidden in (
            self.btn_delete,
            self.btn_duplicate,
            self.btn_enable,
            self.btn_disable,
            self.btn_refresh,
            self.btn_export,
        ):
            hidden.hide()

        self.btn_more = ToolbarOverflowButton()
        self.btn_more.add_actions(
            (
                ("Izbriši", self.delete_clicked.emit),
                ("Podvoji", self.duplicate_clicked.emit),
                ("Omogoči", self.enable_clicked.emit),
                ("Onemogoči", self.disable_clicked.emit),
                ("Osveži", self.refresh_clicked.emit),
                ("Izvoz", self.export_clicked.emit),
            )
        )

        for button, signal in (
            (self.btn_new, self.new_clicked),
            (self.btn_edit, self.edit_clicked),
            (self.btn_run, self.run_clicked),
            (self.btn_delete, self.delete_clicked),
            (self.btn_duplicate, self.duplicate_clicked),
            (self.btn_enable, self.enable_clicked),
            (self.btn_disable, self.disable_clicked),
            (self.btn_refresh, self.refresh_clicked),
            (self.btn_export, self.export_clicked),
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            button.clicked.connect(signal.emit)

        for button in (self.btn_new, self.btn_edit, self.btn_run):
            actions.addWidget(button)
        actions.addStretch(1)
        actions.addWidget(self.btn_more)

        root.addLayout(filters)
        root.addLayout(actions)

        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.trigger.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.enabled.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.log_result.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
