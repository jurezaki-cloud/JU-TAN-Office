from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QMenu, QPushButton, QWidget

from app.core.ui.icons import apply_button_icon


class ToolbarActions(QWidget):
    new_invoice_clicked = Signal()
    new_customer_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarActions")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_invoice = QPushButton("Nov račun")
        self.btn_invoice.setObjectName("PrimaryButton")
        self.btn_invoice.setFixedHeight(36)
        self.btn_invoice.setCursor(Qt.PointingHandCursor)

        self.btn_customer = QPushButton("Nova stranka")
        self.btn_customer.setObjectName("SecondaryButton")
        self.btn_customer.setFixedHeight(36)
        self.btn_customer.setCursor(Qt.PointingHandCursor)

        self.btn_notifications = QPushButton("Obvestila")
        self.btn_notifications.setObjectName("ToolbarIconButton")
        self.btn_notifications.setFixedHeight(36)
        self.btn_notifications.setCursor(Qt.PointingHandCursor)

        self.btn_settings = QPushButton("Nastavitve")
        self.btn_settings.setObjectName("ToolbarIconButton")
        self.btn_settings.setFixedHeight(36)
        self.btn_settings.setCursor(Qt.PointingHandCursor)

        notifications_menu = QMenu(self.btn_notifications)
        empty = notifications_menu.addAction("Ni novih obvestil")
        empty.setEnabled(False)
        self.btn_notifications.setMenu(notifications_menu)

        layout.addWidget(self.btn_invoice)
        layout.addWidget(self.btn_customer)
        layout.addWidget(self.btn_notifications)
        layout.addWidget(self.btn_settings)

        self.btn_invoice.clicked.connect(self.new_invoice_clicked.emit)
        self.btn_customer.clicked.connect(self.new_customer_clicked.emit)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        apply_button_icon(self.btn_invoice, "new")
        apply_button_icon(self.btn_customer, "new")
        apply_button_icon(self.btn_notifications, "info")
        apply_button_icon(self.btn_settings, "edit")
