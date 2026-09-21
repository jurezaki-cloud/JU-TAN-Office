"""Quick action tiles for the enterprise dashboard — UI only."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.theme.tokens import SPACE_2
from app.widgets.cards.enterprise_card import EnterpriseCard


class QuickActionsCard(EnterpriseCard):
    """Premium quick-actions panel wired to existing dashboard signals."""

    new_invoice_requested = Signal()
    new_offer_requested = Signal()
    new_customer_requested = Signal()
    new_article_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("DashboardCard", parent)
        self.body.setSpacing(SPACE_2)

        eyebrow = QLabel("HITRE AKCIJE")
        eyebrow.setObjectName("DashboardEyebrow")
        title = QLabel("Hitri dostop")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Najpogostejša opravila")
        caption.setObjectName("DashboardMuted")

        self.body.addWidget(eyebrow)
        self.body.addWidget(title)
        self.body.addWidget(caption)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        primary = semantic_color("PRIMARY", "#059669")
        muted = semantic_color("TEXT", "#0F172A")

        self.btn_new_invoice = self._make_action(
            "Nov račun",
            "Izdaj dokument",
            "invoices",
            "#FFFFFF",
            "PrimaryButton",
        )
        self.btn_new_offer = self._make_action(
            "Nova ponudba",
            "Pripravi ponudbo",
            "offers",
            muted,
            "SecondaryButton",
        )
        self.btn_new_customer = self._make_action(
            "Nova stranka",
            "Dodaj partnerja",
            "customers",
            muted,
            "SecondaryButton",
        )
        self.btn_new_article = self._make_action(
            "Nov artikel",
            "Vpiši artikel",
            "articles",
            muted,
            "GhostButton",
        )

        # Re-tint primary icon after creation (white on green).
        self.btn_new_invoice.setIcon(brand_icon("invoices", color="#FFFFFF", size=16))
        self.btn_new_offer.setIcon(brand_icon("offers", color=muted, size=16))
        self.btn_new_customer.setIcon(brand_icon("customers", color=muted, size=16))
        self.btn_new_article.setIcon(brand_icon("articles", color=muted, size=16))

        grid.addWidget(self.btn_new_invoice, 0, 0)
        grid.addWidget(self.btn_new_offer, 0, 1)
        grid.addWidget(self.btn_new_customer, 1, 0)
        grid.addWidget(self.btn_new_article, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.body.addWidget(grid_host)
        self.body.addStretch(1)

        self.btn_new_invoice.clicked.connect(self.new_invoice_requested.emit)
        self.btn_new_offer.clicked.connect(self.new_offer_requested.emit)
        self.btn_new_customer.clicked.connect(self.new_customer_requested.emit)
        self.btn_new_article.clicked.connect(self.new_article_requested.emit)

        # Keep reference so theme polish can retint secondary icons if needed.
        self._primary_accent = primary

    @staticmethod
    def _make_action(
        title: str,
        hint: str,
        icon_key: str,
        icon_color: str,
        object_name: str,
    ) -> QPushButton:
        button = QPushButton(f"{title}\n{hint}")
        button.setObjectName(object_name)
        button.setProperty("dashboardAction", True)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(64)
        button.setIcon(brand_icon(icon_key, color=icon_color, size=16))
        return button

    def refresh_icons(self) -> None:
        """Re-apply icon colors after light/dark theme switch."""
        muted = semantic_color("TEXT", "#0F172A")
        self.btn_new_invoice.setIcon(brand_icon("invoices", color="#FFFFFF", size=16))
        self.btn_new_offer.setIcon(brand_icon("offers", color=muted, size=16))
        self.btn_new_customer.setIcon(brand_icon("customers", color=muted, size=16))
        self.btn_new_article.setIcon(brand_icon("articles", color=muted, size=16))
