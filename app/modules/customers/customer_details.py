from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)


class CustomerDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.customer_id = None

        layout = QVBoxLayout(self)

        title = QLabel("Podrobnosti stranke")
        title.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
            padding-bottom:10px;
        """)
        layout.addWidget(title)

        group = QGroupBox("Osnovni podatki")

        form = QFormLayout(group)

        self.company = QLabel("-")
        self.contact = QLabel("-")
        self.address = QLabel("-")
        self.postal_code = QLabel("-")
        self.city = QLabel("-")
        self.country = QLabel("-")
        self.tax = QLabel("-")
        self.email = QLabel("-")
        self.phone = QLabel("-")

        form.addRow("Podjetje:", self.company)
        form.addRow("Kontakt:", self.contact)
        form.addRow("Naslov:", self.address)
        form.addRow("Poštna št.:", self.postal_code)
        form.addRow("Kraj:", self.city)
        form.addRow("Država:", self.country)
        form.addRow("Davčna št.:", self.tax)
        form.addRow("E-pošta:", self.email)
        form.addRow("Telefon:", self.phone)

        layout.addWidget(group)

        self.editButton = QPushButton("✏️ Uredi stranko")
        layout.addWidget(self.editButton)

        layout.addStretch()

    def load_customer(self, row):

        if row is None:
            return

        self.customer_id = row[0]

        self.company.setText(row[1] or "")
        self.contact.setText(row[2] or "")
        self.address.setText(row[3] or "")
        self.postal_code.setText(row[4] or "")
        self.city.setText(row[5] or "")
        self.country.setText(row[6] or "")
        self.tax.setText(row[7] or "")
        self.email.setText(row[8] or "")
        self.phone.setText(row[9] or "")

    def clear(self):
        self.customer_id = None
        for label in (
            self.company, self.contact, self.address, self.postal_code,
            self.city, self.country, self.tax, self.email, self.phone,
        ):
            label.setText("-")
