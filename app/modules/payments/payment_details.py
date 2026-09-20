from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.invoices.status_badge import invoice_badge


class PaymentDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.invoice_id = None
        self.setObjectName("PaymentDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti terjatve")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.lblNumber = QLabel("-")
        self.lblCustomer = QLabel("-")
        self.lblDate = QLabel("-")
        self.lblDue = QLabel("-")
        self.lblStatus = QLabel("-")
        self.lblTotal = QLabel("0.00 €")

        for label in (
            self.lblNumber,
            self.lblCustomer,
            self.lblDate,
            self.lblDue,
            self.lblStatus,
            self.lblTotal,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Račun", self.lblNumber)
        form.addRow("Stranka", self.lblCustomer)
        form.addRow("Datum", self.lblDate)
        form.addRow("Rok", self.lblDue)
        form.addRow("Status", self.lblStatus)
        form.addRow("Znesek", self.lblTotal)
        card.body.addLayout(form)

        self.payButton = QPushButton("Zabeleži plačilo")
        self.payButton.setObjectName("PrimaryButton")
        self.invoiceButton = QPushButton("Odpri račun")
        self.invoiceButton.setObjectName("SecondaryButton")
        self.payButton.setMinimumHeight(36)
        self.invoiceButton.setMinimumHeight(36)
        card.body.addWidget(self.payButton)
        card.body.addWidget(self.invoiceButton)
        card.body.addStretch()
        layout.addWidget(card)

    def clear(self):
        self.invoice_id = None
        self.lblNumber.setText("-")
        self.lblCustomer.setText("-")
        self.lblDate.setText("-")
        self.lblDue.setText("-")
        self.lblStatus.setText("-")
        self.lblTotal.setText("0.00 €")

    def load_row(self, row):
        self.invoice_id = row[0]
        self.lblNumber.setText(str(row[1]))
        self.lblCustomer.setText(str(row[2]))
        self.lblDate.setText(str(row[3]))
        self.lblDue.setText(str(row[4] or "-"))
        self.lblStatus.setText(invoice_badge(row[6], row[4]))
        try:
            self.lblTotal.setText(f"{float(row[5]):,.2f} €".replace(",", " "))
        except (TypeError, ValueError):
            self.lblTotal.setText("0.00 €")
