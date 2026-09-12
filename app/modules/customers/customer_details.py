from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class CustomerDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.customer_id = None
        self.setObjectName("CustomerDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti stranke")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.company = QLabel("-")
        self.contact = QLabel("-")
        self.address = QLabel("-")
        self.postal_code = QLabel("-")
        self.city = QLabel("-")
        self.country = QLabel("-")
        self.tax = QLabel("-")
        self.email = QLabel("-")
        self.phone = QLabel("-")

        for label in (
            self.company,
            self.contact,
            self.address,
            self.postal_code,
            self.city,
            self.country,
            self.tax,
            self.email,
            self.phone,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Podjetje", self.company)
        form.addRow("Kontakt", self.contact)
        form.addRow("Naslov", self.address)
        form.addRow("Poštna št.", self.postal_code)
        form.addRow("Kraj", self.city)
        form.addRow("Država", self.country)
        form.addRow("Davčna št.", self.tax)
        form.addRow("E-pošta", self.email)
        form.addRow("Telefon", self.phone)

        card.body.addLayout(form)

        self.editButton = QPushButton("Uredi stranko")
        self.editButton.setObjectName("SecondaryButton")
        self.editButton.setMinimumHeight(36)
        card.body.addWidget(self.editButton)
        card.body.addStretch()

        layout.addWidget(card)

    def clear(self):
        self.load_customer(None)

    def load_customer(self, row):

        if row is None:
            self.customer_id = None
            for label in (
                self.company,
                self.contact,
                self.address,
                self.postal_code,
                self.city,
                self.country,
                self.tax,
                self.email,
                self.phone,
            ):
                label.setText("-")
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
