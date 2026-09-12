from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.core.permissions import ROLES
from app.core.ui.form_grid import FormGrid
from app.widgets.cards.enterprise_card import EnterpriseCard


class SecurityCard(QWidget):
    password_clicked = Signal()
    logout_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Varnost in seje")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)
        grid = FormGrid()
        self.role = QComboBox()
        self.role.addItems(list(ROLES))
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 240)
        self.timeout.setValue(30)
        self.timeout.setSuffix(" min")
        self.old = QLineEdit()
        self.old.setEchoMode(QLineEdit.Password)
        self.new = QLineEdit()
        self.new.setEchoMode(QLineEdit.Password)
        grid.add("Vloga", self.role, "Timeout", self.timeout)
        grid.add("Staro geslo", self.old, "Novo geslo", self.new)
        card.body.addLayout(grid.layout)
        self.btn_password = QPushButton("Spremeni geslo")
        self.btn_password.setObjectName("SecondaryButton")
        self.btn_logout = QPushButton("Odjava")
        self.btn_logout.setObjectName("SecondaryButton")
        self.btn_password.clicked.connect(self.password_clicked.emit)
        self.btn_logout.clicked.connect(self.logout_clicked.emit)
        card.body.addWidget(self.btn_password)
        card.body.addWidget(self.btn_logout)
        layout.addWidget(card)

    def values(self) -> dict:
        return {
            "role": self.role.currentText(),
            "session_timeout_min": self.timeout.value(),
        }

    def set_values(self, extras: dict) -> None:
        role = extras.get("role") or "Administrator"
        index = self.role.findText(role)
        if index >= 0:
            self.role.setCurrentIndex(index)
        self.timeout.setValue(int(extras.get("session_timeout_min") or 30))
