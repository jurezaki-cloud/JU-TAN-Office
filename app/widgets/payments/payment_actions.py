from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget


class PaymentActions(QWidget):
    new_clicked = Signal()
    unpaid_clicked = Signal()
    invoice_clicked = Signal()
    refresh_clicked = Signal()
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PaymentActions")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.filter = QComboBox()
        self.filter.setObjectName("EnterpriseFilter")
        self.filter.setMinimumHeight(36)
        self.filter.addItem("Vsa plačila", "all")
        self.filter.addItem("Plačano", "Plačano")
        self.filter.addItem("Neplačano", "Neplačano")
        self.filter.addItem("Zapadlo", "Zapadlo")

        self.btn_new = QPushButton("Zabeleži plačilo")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_unpaid = QPushButton("Označi neplačano")
        self.btn_unpaid.setObjectName("SecondaryButton")
        self.btn_invoice = QPushButton("Odpri račun")
        self.btn_invoice.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")

        layout.addWidget(self.filter)
        for button in (
            self.btn_new,
            self.btn_unpaid,
            self.btn_invoice,
            self.btn_refresh,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_new.clicked.connect(self.new_clicked.emit)
        self.btn_unpaid.clicked.connect(self.unpaid_clicked.emit)
        self.btn_invoice.clicked.connect(self.invoice_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.filter.currentIndexChanged.connect(
            lambda: self.filter_changed.emit(self.filter.currentData())
        )
