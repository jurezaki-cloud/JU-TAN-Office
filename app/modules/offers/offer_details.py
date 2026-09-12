from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class OfferDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.offer_id = None
        self.setObjectName("OfferDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti ponudbe")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.lblNumber = QLabel("-")
        self.lblCustomer = QLabel("-")
        self.lblDate = QLabel("-")
        self.lblValid = QLabel("-")
        self.lblStatus = QLabel("-")
        self.lblTotal = QLabel("0.00 €")

        for label in (
            self.lblNumber,
            self.lblCustomer,
            self.lblDate,
            self.lblValid,
            self.lblStatus,
            self.lblTotal,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Številka", self.lblNumber)
        form.addRow("Stranka", self.lblCustomer)
        form.addRow("Datum", self.lblDate)
        form.addRow("Velja do", self.lblValid)
        form.addRow("Status", self.lblStatus)
        form.addRow("Skupaj", self.lblTotal)
        card.body.addLayout(form)

        self.editButton = QPushButton("Uredi ponudbo")
        self.editButton.setObjectName("SecondaryButton")
        self.deleteButton = QPushButton("Izbriši ponudbo")
        self.deleteButton.setObjectName("DangerButton")
        self.editButton.setMinimumHeight(36)
        self.deleteButton.setMinimumHeight(36)
        card.body.addWidget(self.editButton)
        card.body.addWidget(self.deleteButton)
        card.body.addStretch()

        layout.addWidget(card)

    def clear(self):

        self.offer_id = None

        self.lblNumber.setText("-")
        self.lblCustomer.setText("-")
        self.lblDate.setText("-")
        self.lblValid.setText("-")
        self.lblStatus.setText("-")
        self.lblTotal.setText("0.00 €")

    def load_offer(self, offer):

        self.offer_id = offer[0]

        self.lblNumber.setText(str(offer[1]))
        self.lblCustomer.setText(str(offer[2]))
        self.lblDate.setText(str(offer[3]))
        self.lblValid.setText(str(offer[4]))
        self.lblStatus.setText(str(offer[5]))

        if len(offer) > 9:
            total = offer[9]
        else:
            total = offer[6]

        try:
            self.lblTotal.setText(f"{float(total):.2f} €")
        except (TypeError, ValueError):
            self.lblTotal.setText("0.00 €")
