from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QMenu, QPushButton, QWidget

from app.core.permissions import can, can_open_page
from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.widgets.navigation.navigation import PAGE_INDEX


class ToolbarActions(QWidget):
    """Global + Novo menu + secondary shell actions."""

    new_invoice_clicked = Signal()
    new_offer_clicked = Signal()
    new_order_clicked = Signal()
    new_customer_clicked = Signal()
    settings_clicked = Signal()
    lock_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarActions")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Text "+ Novo" only — no plus icon (avoids "+ + Novo").
        self.btn_new = QPushButton("+ Novo")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setFixedHeight(34)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setToolTip("Ustvari nov dokument")

        self._new_menu = QMenu(self.btn_new)
        self._new_menu.setObjectName("NewMenu")
        self.btn_new.setMenu(self._new_menu)
        self._rebuild_new_menu()

        muted = semantic_color("TEXT_MUTED", "#64748B")

        self.btn_lock = QPushButton()
        self.btn_lock.setObjectName("ToolbarIconButton")
        self.btn_lock.setFixedSize(34, 34)
        self.btn_lock.setCursor(Qt.PointingHandCursor)
        self.btn_lock.setToolTip("Zakleni")
        self.btn_lock.setIcon(brand_icon("lock", color=muted, size=16))
        self.btn_lock.clicked.connect(self.lock_clicked.emit)

        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("ToolbarIconButton")
        self.btn_settings.setFixedSize(34, 34)
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setToolTip("Nastavitve")
        self.btn_settings.setIcon(brand_icon("settings", color=muted, size=16))
        self.btn_settings.clicked.connect(self.settings_clicked.emit)

        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_lock)
        layout.addWidget(self.btn_settings)

    def _rebuild_new_menu(self) -> None:
        self._new_menu.clear()
        writable = can("write")
        icon_color = semantic_color("TEXT", "#0F172A")
        entries = [
            ("Nov račun", "invoices", self.new_invoice_clicked, "invoices"),
            ("Nova ponudba", "offers", self.new_offer_clicked, "offers"),
            ("Novo naročilo", "orders", self.new_order_clicked, "orders"),
            ("Nova stranka", "customers", self.new_customer_clicked, "customers"),
        ]
        any_visible = False
        for label, page_key, signal, icon_key in entries:
            page_idx = PAGE_INDEX.get(page_key)
            if page_idx is None or not can_open_page(page_idx) or not writable:
                continue
            action = self._new_menu.addAction(
                brand_icon(icon_key, color=icon_color, size=16), label
            )
            action.triggered.connect(signal.emit)
            any_visible = True
        self.btn_new.setEnabled(any_visible)
        self.btn_new.setVisible(any_visible or writable)

    def refresh_permissions(self) -> None:
        self._rebuild_new_menu()
        muted = semantic_color("TEXT_MUTED", "#64748B")
        self.btn_lock.setIcon(brand_icon("lock", color=muted, size=16))
        self.btn_settings.setIcon(brand_icon("settings", color=muted, size=16))
        self.btn_settings.setVisible(can_open_page(PAGE_INDEX["settings"]))
