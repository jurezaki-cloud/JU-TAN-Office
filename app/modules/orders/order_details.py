from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard


class OrderDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.order_id = None
        self.setObjectName("OrderDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti naročila")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.lblNumber = QLabel("-")
        self.lblCustomer = QLabel("-")
        self.lblDate = QLabel("-")
        self.lblDelivery = QLabel("-")
        self.lblStatus = QLabel("-")
        self.lblTotal = QLabel("0.00 €")

        for label in (
            self.lblNumber,
            self.lblCustomer,
            self.lblDate,
            self.lblDelivery,
            self.lblStatus,
            self.lblTotal,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Številka", self.lblNumber)
        form.addRow("Stranka", self.lblCustomer)
        form.addRow("Datum", self.lblDate)
        form.addRow("Dobava", self.lblDelivery)
        form.addRow("Status", self.lblStatus)
        form.addRow("Skupaj", self.lblTotal)
        card.body.addLayout(form)

        self.editButton = QPushButton("Uredi naročilo")
        self.editButton.setObjectName("SecondaryButton")
        self.deleteButton = QPushButton("Izbriši naročilo")
        self.deleteButton.setObjectName("DangerButton")
        self.editButton.setMinimumHeight(36)
        self.deleteButton.setMinimumHeight(36)
        card.body.addWidget(self.editButton)
        card.body.addWidget(self.deleteButton)
        card.body.addStretch()
        layout.addWidget(card)

    def clear(self):
        self.order_id = None
        self.lblNumber.setText("-")
        self.lblCustomer.setText("-")
        self.lblDate.setText("-")
        self.lblDelivery.setText("-")
        self.lblStatus.setText("-")
        self.lblTotal.setText("0.00 €")

    def load_order(self, order):
        self.order_id = order[0]
        self.lblNumber.setText(str(order[1]))
        self.lblCustomer.setText(str(order[2]))
        self.lblDate.setText(str(order[3]))
        self.lblDelivery.setText(str(order[4] or "-"))
        self.lblStatus.setText(str(order[5]))
        try:
            self.lblTotal.setText(f"{float(order[6]):.2f} €")
        except (TypeError, ValueError, IndexError):
            self.lblTotal.setText("0.00 €")
