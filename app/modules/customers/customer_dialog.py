from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)


class CustomerDialog(QDialog):

    def __init__(self, parent=None, customer=None):
        super().__init__(parent)

        self.customer = customer

        self.setWindowTitle(
            "Uredi stranko" if customer else "Nova stranka"
        )
        self.resize(500, 500)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.company = QLineEdit()
        self.contact = QLineEdit()
        self.address = QLineEdit()
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.country = QLineEdit()
        self.tax_number = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()

        form.addRow("Podjetje:", self.company)
        form.addRow("Kontakt:", self.contact)
        form.addRow("Naslov:", self.address)
        form.addRow("Poštna št.:", self.postal_code)
        form.addRow("Kraj:", self.city)
        form.addRow("Država:", self.country)
        form.addRow("Davčna št.:", self.tax_number)
        form.addRow("E-pošta:", self.email)
        form.addRow("Telefon:", self.phone)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Prekliči")
        btn_save = QPushButton("Shrani")

        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        if customer:
            self.company.setText(customer.get("company", ""))
            self.contact.setText(customer.get("contact", ""))
            self.address.setText(customer.get("address", ""))
            self.postal_code.setText(customer.get("postal_code", ""))
            self.city.setText(customer.get("city", ""))
            self.country.setText(customer.get("country", ""))
            self.tax_number.setText(customer.get("tax_number", ""))
            self.email.setText(customer.get("email", ""))
            self.phone.setText(customer.get("phone", ""))

    def get_data(self):
        return {
            "company": self.company.text().strip(),
            "contact": self.contact.text().strip(),
            "address": self.address.text().strip(),
            "postal_code": self.postal_code.text().strip(),
            "city": self.city.text().strip(),
            "country": self.country.text().strip(),
            "tax_number": self.tax_number.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
        }