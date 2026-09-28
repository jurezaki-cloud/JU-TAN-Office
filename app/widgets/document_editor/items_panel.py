"""Premium document items area for invoice / offer / order editors."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.icons import apply_button_icon
from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
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
        header.setSpacing(12)

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
        self.btn_add_item = QPushButton("Dodaj postavko")
        self.btn_add_item.setObjectName("PrimaryButton")
        self.btn_add_item.setToolTip("Dodaj artikel ali storitev na dokument")
        self.btn_remove_item = QPushButton("Odstrani")
        self.btn_remove_item.setObjectName("DangerButton")
        self.btn_remove_item.setToolTip("Odstrani izbrano postavko")
        for button in (self.btn_add_item, self.btn_remove_item):
            button.setMinimumHeight(36)
            button.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(button)
        apply_button_icon(self.btn_add_item, "new")
        apply_button_icon(self.btn_remove_item, "delete")

        header.addLayout(title_col, 1)
        header.addLayout(toolbar, 0)
        self.body.addLayout(header)

        self.lbl_add_hint = QLabel("")
        self.lbl_add_hint.setObjectName("DocumentItemsHint")
        self.lbl_add_hint.setWordWrap(True)
        self.lbl_add_hint.hide()
        self.body.addWidget(self.lbl_add_hint)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("DocumentItemsStack")

        table_wrap = QWidget()
        table_wrap.setObjectName("DocumentItemsTableWrap")
        wrap_layout = QVBoxLayout(table_wrap)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setSpacing(0)

        self.items_table = InvoiceTable()
        self.items_table.setObjectName("DocumentItemsTable")
        self.items_table.setMinimumHeight(220)
        self.items_table.verticalHeader().setDefaultSectionSize(44)
        wrap_layout.addWidget(self.items_table)
        self.content_stack.addWidget(table_wrap)

        self.empty_state = self._build_empty_state()
        self.content_stack.addWidget(self.empty_state)
        self.body.addWidget(self.content_stack, 1)

        self._item_count = 0
        self.set_item_count(0)

    def _build_empty_state(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("DocumentItemsEmpty")
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(8)

        icon = QLabel()
        icon.setObjectName("DocumentItemsEmptyIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(
            brand_icon(
                "new",
                color=semantic_color("TEXT_MUTED", "#64748B"),
                size=28,
            ).pixmap(28, 28)
        )

        title = QLabel("Ni dodanih postavk")
        title.setObjectName("DocumentItemsEmptyTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Dodajte prvi artikel ali storitev na dokument.")
        subtitle.setObjectName("DocumentItemsEmptySubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        self.btn_empty_add = QPushButton("Dodaj postavko")
        self.btn_empty_add.setObjectName("PrimaryButton")
        self.btn_empty_add.setMinimumHeight(36)
        self.btn_empty_add.setCursor(Qt.PointingHandCursor)
        apply_button_icon(self.btn_empty_add, "new")
        self.btn_empty_add.clicked.connect(self.btn_add_item.click)

        layout.addStretch(1)
        layout.addWidget(icon, 0, Qt.AlignHCenter)
        layout.addSpacing(4)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.btn_empty_add, 0, Qt.AlignHCenter)
        layout.addStretch(1)
        return frame

    def set_item_count(self, count: int) -> None:
        n = max(0, int(count or 0))
        self._item_count = n
        if n == 1:
            self.lbl_count.setText("1 postavka")
        elif 2 <= n <= 4:
            self.lbl_count.setText(f"{n} postavke")
        else:
            self.lbl_count.setText(f"{n} postavk")

        show_empty = n == 0
        self.content_stack.setCurrentWidget(self.empty_state if show_empty else self.content_stack.widget(0))
        self.btn_remove_item.setEnabled(n > 0 and self.btn_add_item.isEnabled())

    def set_add_enabled(self, enabled: bool, *, reason: str | None = None) -> None:
        """Enable/disable add actions and show a clear reason when blocked."""
        self.btn_add_item.setEnabled(enabled)
        self.btn_empty_add.setEnabled(enabled)
        self.btn_remove_item.setEnabled(enabled and self._item_count > 0)
        hint = (reason or "").strip()
        if enabled or not hint:
            self.lbl_add_hint.hide()
            self.lbl_add_hint.clear()
            self.btn_add_item.setToolTip("Dodaj artikel ali storitev na dokument")
            self.btn_empty_add.setToolTip("Dodaj artikel ali storitev na dokument")
            return
        self.lbl_add_hint.setText(hint)
        self.lbl_add_hint.show()
        self.btn_add_item.setToolTip(hint)
        self.btn_empty_add.setToolTip(hint)
