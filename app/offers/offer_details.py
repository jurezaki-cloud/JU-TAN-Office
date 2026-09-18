from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)


class OfferDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.offer_id = None

        layout = QVBoxLayout(self)

        title = QLabel("Podrobnosti ponudbe")
        title.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
            padding-bottom:10px;
        """)
        layout.addWidget(title)

        self.lblNumber = QLabel("-")
        self.lblCustomer = QLabel("-")
        self.lblDate = QLabel("-")
        self.lblValid = QLabel("-")
        self.lblStatus = QLabel("-")
        self.lblTotal = QLabel("0.00 €")

        layout.addWidget(QLabel("Številka"))
        layout.addWidget(self.lblNumber)

        layout.addWidget(QLabel("Stranka"))
        layout.addWidget(self.lblCustomer)

        layout.addWidget(QLabel("Datum"))
        layout.addWidget(self.lblDate)

        layout.addWidget(QLabel("Velja do"))
        layout.addWidget(self.lblValid)

        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.lblStatus)

        layout.addWidget(QLabel("Skupaj"))
        layout.addWidget(self.lblTotal)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        self.editButton = QPushButton("✏ Uredi ponudbo")
        self.deleteButton = QPushButton("🗑 Izbriši ponudbo")

        layout.addWidget(self.editButton)
        layout.addWidget(self.deleteButton)

        layout.addStretch()

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
        self.lblTotal.setText(f"{offer[6]:.2f} €")
