"""Premium welcome header for the enterprise dashboard — UI only."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from app.core.session import session
from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.theme.tokens import SPACE_2, SPACE_3
from app.widgets.cards.enterprise_card import EnterpriseCard

SLO_MONTHS_FULL = (
    "januar", "februar", "marec", "april", "maj", "junij",
    "julij", "avgust", "september", "oktober", "november", "december",
)
SLO_WEEKDAYS = (
    "ponedeljek", "torek", "sreda", "četrtek",
    "petek", "sobota", "nedelja",
)


class WelcomeHeader(EnterpriseCard):
    """Professional greeting strip with company, user, and date."""

    def __init__(self, parent=None):
        super().__init__("DashboardWelcomeCard", parent)
        self.body.setContentsMargins(22, 18, 22, 18)
        self.body.setSpacing(SPACE_2)
        self.setMinimumHeight(96)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE_3)

        icon = QLabel()
        icon.setObjectName("DashboardWelcomeIcon")
        icon.setFixedSize(44, 44)
        icon.setAlignment(Qt.AlignCenter)
        icon.setPixmap(
            brand_icon("dashboard", color=semantic_color("PRIMARY", "#059669"), size=22).pixmap(22, 22)
        )
        self._icon = icon

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)

        self.eyebrow = QLabel("JU-TAN OFFICE")
        self.eyebrow.setObjectName("DashboardEyebrow")

        self.title = QLabel("Dobrodošli")
        self.title.setObjectName("DashboardWelcome")

        self.subtitle = QLabel("Pregled poslovanja in ključnih kazalnikov")
        self.subtitle.setObjectName("DashboardMuted")
        self.subtitle.setWordWrap(True)

        text.addWidget(self.eyebrow)
        text.addWidget(self.title)
        text.addWidget(self.subtitle)

        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(2)

        self.date_label = QLabel("")
        self.date_label.setObjectName("DashboardDate")
        self.date_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.role_label = QLabel("")
        self.role_label.setObjectName("DashboardWelcomeMeta")
        self.role_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        meta.addWidget(self.date_label)
        meta.addWidget(self.role_label)
        meta.addStretch()

        row.addWidget(icon, 0, Qt.AlignTop)
        row.addLayout(text, 1)
        row.addLayout(meta, 0)
        self.body.addLayout(row)
        # Session/company fill is deferred to Dashboard.refresh() / showEvent.

    def refresh(self) -> None:
        user = (getattr(session, "user", None) or "").strip() or "uporabnik"
        role = (getattr(session, "role", None) or "").strip() or "—"
        company = self._company_name()

        self.title.setText(f"Dobrodošli, {user}")
        if company:
            self.subtitle.setText(f"{company} · Pregled poslovanja")
        else:
            self.subtitle.setText("Pregled poslovanja in ključnih kazalnikov")

        today = date.today()
        weekday = SLO_WEEKDAYS[today.weekday()].capitalize()
        month = SLO_MONTHS_FULL[today.month - 1]
        self.date_label.setText(f"{weekday}, {today.day}. {month} {today.year}")
        self.role_label.setText(role)

        # Re-tint icon for current theme (light/dark).
        self._icon.setPixmap(
            brand_icon(
                "dashboard",
                color=semantic_color("PRIMARY", "#059669"),
                size=22,
            ).pixmap(22, 22)
        )

    @staticmethod
    def _company_name() -> str:
        try:
            from app.database.company_repository import company_repository

            row = company_repository.get_company()
            if not row:
                return ""
            name = (row[1] or row[2] or "").strip()
            return name
        except Exception:
            return ""
