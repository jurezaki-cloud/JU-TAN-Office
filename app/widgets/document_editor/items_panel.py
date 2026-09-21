"""Premium document items area for invoice / offer / order editors."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.ui.icons import apply_button_icon
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.invoices.invoice_table import InvoiceTable


class DocumentItemsPanel(EnterpriseCard):
    """Items table with modern toolbar — reuses InvoiceTable / InvoiceItemsModel."""

    def __init__(self, parent=None) -> None:
        super().__init__("DocumentEditorCard", parent)
        self.setObjectName("DocumentItemsPanel")
        self.body.setContentsMargins(16, 14, 16, 14)
        self.body.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)
        eyebrow = QLabel("POSTAVKE")
        eyebrow.setObjectName("DocumentEditorEyebrow")
        title = QLabel("Vrstice dokumenta")
        title.setObjectName("DocumentSectionTitle")
        self.lbl_count = QLabel("0 postavk")
        self.lbl_count.setObjectName("DashboardMuted")
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        title_col.addWidget(self.lbl_count)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)
        self.btn_add_item = QPushButton("+ Dodaj postavko")
        self.btn_add_item.setObjectName("PrimaryButton")
        self.btn_remove_item = QPushButton("Odstrani")
        self.btn_remove_item.setObjectName("DangerButton")
        for button in (self.btn_add_item, self.btn_remove_item):
            button.setMinimumHeight(36)
            button.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(button)
        apply_button_icon(self.btn_add_item, "new")
        apply_button_icon(self.btn_remove_item, "delete")

        header.addLayout(title_col, 1)
        header.addLayout(toolbar, 0)
        self.body.addLayout(header)

        table_wrap = QWidget()
        table_wrap.setObjectName("DocumentItemsTableWrap")
        wrap_layout = QVBoxLayout(table_wrap)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setSpacing(0)

        self.items_table = InvoiceTable()
        self.items_table.setObjectName("DocumentItemsTable")
        self.items_table.setMinimumHeight(300)
        self.items_table.verticalHeader().setDefaultSectionSize(48)
        wrap_layout.addWidget(self.items_table)
        self.body.addWidget(table_wrap, 1)

    def set_item_count(self, count: int) -> None:
        n = max(0, int(count or 0))
        if n == 1:
            self.lbl_count.setText("1 postavka")
        elif 2 <= n <= 4:
            self.lbl_count.setText(f"{n} postavke")
        else:
            self.lbl_count.setText(f"{n} postavk")
