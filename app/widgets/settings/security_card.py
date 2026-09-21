from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.core.permissions import ROLES
from app.core.ui.form_grid import FormGrid
from app.widgets.cards.enterprise_card import EnterpriseCard


class SecurityCard(QWidget):
    password_clicked = Signal()
    logout_clicked = Signal()
    changed = Signal()

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
        self.remember = QCheckBox("Zapomni uporabniško ime")
        self.remember.setChecked(True)
        card.body.addLayout(grid.layout)
        card.body.addWidget(self.remember)
        self.btn_password = QPushButton("Spremeni geslo")
        self.btn_password.setObjectName("SecondaryButton")
        self.btn_logout = QPushButton("Odjava")
        self.btn_logout.setObjectName("SecondaryButton")
        self.btn_password.clicked.connect(self.password_clicked.emit)
        self.btn_logout.clicked.connect(self.logout_clicked.emit)
        self.role.currentTextChanged.connect(self._emit_changed)
        self.timeout.valueChanged.connect(self._emit_changed)
        self.remember.toggled.connect(self._emit_changed)
        card.body.addWidget(self.btn_password)
        card.body.addWidget(self.btn_logout)
        layout.addWidget(card)

    def _emit_changed(self, *_args) -> None:
        self.changed.emit()

    def values(self) -> dict:
        return {
            "role": self.role.currentText(),
            "session_timeout_min": self.timeout.value(),
            "remember_user": self.remember.isChecked(),
        }

    def set_values(self, extras: dict) -> None:
        from app.core.permissions import can

        self.role.blockSignals(True)
        self.timeout.blockSignals(True)
        self.remember.blockSignals(True)
        try:
            role = extras.get("role") or "Administrator"
            index = self.role.findText(role)
            if index >= 0:
                self.role.setCurrentIndex(index)
            self.role.setEnabled(can("users"))
            self.timeout.setValue(int(extras.get("session_timeout_min") or 30))
            self.remember.setChecked(bool(extras.get("remember_user", True)))
        finally:
            self.role.blockSignals(False)
            self.timeout.blockSignals(False)
            self.remember.blockSignals(False)
