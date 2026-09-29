from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.services.mail_center import mail_center
from app.widgets.cards.enterprise_card import EnterpriseCard


class MailCard(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = EnterpriseCard("DashboardCard")
        title = QLabel("JU-TAN Mail Center")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)
        hint = QLabel("SMTP nastavitve za neposredno pošiljanje dokumentov strankam.")
        hint.setObjectName("DashboardMuted")
        card.body.addWidget(hint)
        form = QFormLayout()
        self.host = QLineEdit()
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(587)
        self.security = QComboBox(); self.security.addItems(["STARTTLS", "SSL", "NONE"])
        self.username = QLineEdit()
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        self.sender_name = QLineEdit()
        self.sender_email = QLineEdit()
        self.reply_to = QLineEdit()
        form.addRow("SMTP strežnik", self.host)
        form.addRow("Vrata", self.port)
        form.addRow("Zaščita", self.security)
        form.addRow("Uporabniško ime", self.username)
        form.addRow("Geslo / app password", self.password)
        form.addRow("Ime pošiljatelja", self.sender_name)
        form.addRow("E-pošta pošiljatelja", self.sender_email)
        form.addRow("Reply-To", self.reply_to)
        card.body.addLayout(form)
        self.btn_test = QPushButton("Preveri SMTP povezavo")
        self.btn_test.setObjectName("SecondaryButton")
        self.btn_test.clicked.connect(self._test)
        card.body.addWidget(self.btn_test)
        layout.addWidget(card)
        for field in (self.host, self.username, self.password, self.sender_name, self.sender_email, self.reply_to):
            field.textChanged.connect(self.changed.emit)
        self.port.valueChanged.connect(self.changed.emit)
        self.security.currentTextChanged.connect(self.changed.emit)

    def values(self):
        return {
            "host": self.host.text().strip(), "port": self.port.value(),
            "security": self.security.currentText(), "username": self.username.text().strip(),
            "sender_name": self.sender_name.text().strip(), "sender_email": self.sender_email.text().strip(),
            "reply_to": self.reply_to.text().strip(),
        }

    def password_value(self):
        return self.password.text()

    def set_values(self, data, password=""):
        self.host.setText(str(data.get("host") or ""))
        self.port.setValue(int(data.get("port") or 587))
        self.security.setCurrentText(str(data.get("security") or "STARTTLS"))
        self.username.setText(str(data.get("username") or ""))
        # Stored SMTP secrets are never decrypted back into a visible UI field.
        self.password.clear()
        self.password.setPlaceholderText("Shranjeno geslo ostane nespremenjeno")
        self.sender_name.setText(str(data.get("sender_name") or ""))
        self.sender_email.setText(str(data.get("sender_email") or ""))
        self.reply_to.setText(str(data.get("reply_to") or ""))

    def _test(self):
        QMessageBox.information(self, "Mail Center", "Najprej shranite nastavitve, nato lahko povezavo preverite v oknu za pošiljanje dokumenta.")
