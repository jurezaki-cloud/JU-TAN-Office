from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QTextEdit,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.widgets.cards.enterprise_card import EnterpriseCard


class SupplierDialog(EnterpriseDialog):

    def __init__(self, parent=None, data: dict | None = None) -> None:
        title = "Uredi dobavitelja" if data else "Nov dobavitelj"
        super().__init__(parent, title=title, heading=title, size="SMALL", state_key="dialog.supplier")
        self.setObjectName("SupplierDialog")
        self.bind_save(self._accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.name = QLineEdit()
        self.tax_number = QLineEdit()
        self.contact = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.status = QComboBox()
        self.status.setObjectName("EnterpriseFilter")
        self.status.addItems(["Active", "Inactive"])
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)
        for field in (self.name, self.tax_number, self.contact, self.phone, self.email):
            field.setObjectName("EnterpriseSearch")
            field.setMinimumHeight(36)
        grid.add("Naziv", self.name, "Davčna", self.tax_number)
        grid.add("Kontakt", self.contact, "Telefon", self.phone)
        grid.add("Email", self.email, "Status", self.status)
        grid.add_full("Opombe", self.notes)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        if data:
            self.name.setText(data.get("name", ""))
            self.tax_number.setText(data.get("tax_number", ""))
            self.contact.setText(data.get("contact", ""))
            self.phone.setText(data.get("phone", ""))
            self.email.setText(data.get("email", ""))
            index = self.status.findText(data.get("status") or "Active")
            if index >= 0:
                self.status.setCurrentIndex(index)
            self.notes.setPlainText(data.get("notes", ""))

    def _accept(self) -> None:
        if not self.name.text().strip():
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "tax_number": self.tax_number.text().strip(),
            "contact": self.contact.text().strip(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
