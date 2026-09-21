"""Privacy / GDPR settings card — UI surface only (placeholders, no data pipeline)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.docs_paths import privacy_policy_path
from app.core.ui.notify import toast
from app.utils.vat import WEBSITE_LABEL, WEBSITE_URL
from app.widgets.cards.enterprise_card import EnterpriseCard

# Fallback when local PRIVACY.md is not packaged yet.
PRIVACY_POLICY_URL = "https://www.ju-tan.com"


class PrivacyCard(QWidget):
    """Commercial privacy / GDPR information and placeholder data actions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        card.body.setContentsMargins(22, 22, 22, 22)
        card.body.setSpacing(16)

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        eyebrow = QLabel("PRIVACY & GDPR")
        eyebrow.setObjectName("LicenseEyebrow")

        title = QLabel("Zasebnost")
        title.setObjectName("LicenseCardTitle")

        caption = QLabel(
            "Informacije o obdelavi podatkov, izvozu in upravljanju osebnih podatkov"
        )
        caption.setObjectName("DashboardMuted")
        caption.setWordWrap(True)

        header.addWidget(eyebrow)
        header.addWidget(title)
        header.addWidget(caption)
        card.body.addLayout(header)

        info = QFrame()
        info.setObjectName("LicenseHero")
        info.setAttribute(Qt.WA_StyledBackground, True)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(8)

        info_title = QLabel("Obdelava podatkov")
        info_title.setObjectName("LicenseMetaCaption")

        self.lbl_privacy_info = QLabel(
            "JU-TAN Office hrani poslovne podatke lokalno na vaši napravi. "
            "Osebni podatki strank in dokumentov se ne pošiljajo na zunanje strežnike "
            "razen kjer to zahteva aktivacija licence ali vaša lastna konfiguracija."
        )
        self.lbl_privacy_info.setObjectName("DashboardMuted")
        self.lbl_privacy_info.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(self.lbl_privacy_info)
        card.body.addWidget(info)

        # —— Data management ——
        manage_title = QLabel("Upravljanje podatkov")
        manage_title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(manage_title)

        manage_hint = QLabel(
            "Izvoz in zahteve po izbrisu so pripravljene kot komercialni vmesnik. "
            "Celovit GDPR izvoz bo na voljo v naslednji fazi."
        )
        manage_hint.setObjectName("DashboardMuted")
        manage_hint.setWordWrap(True)
        card.body.addWidget(manage_hint)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        actions.setSpacing(10)

        self.btn_export = QPushButton("Izvozi podatke")
        self.btn_export.setObjectName("PrimaryButton")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setMinimumHeight(38)
        self.btn_export.clicked.connect(self._export_placeholder)

        self.btn_policy = QPushButton("Politika zasebnosti")
        self.btn_policy.setObjectName("SecondaryButton")
        self.btn_policy.setCursor(Qt.PointingHandCursor)
        self.btn_policy.setMinimumHeight(38)
        self.btn_policy.clicked.connect(self._open_policy)

        self.btn_manage = QPushButton("Upravljanje podatkov")
        self.btn_manage.setObjectName("SecondaryButton")
        self.btn_manage.setCursor(Qt.PointingHandCursor)
        self.btn_manage.setMinimumHeight(38)
        self.btn_manage.clicked.connect(self._manage_placeholder)

        actions.addWidget(self.btn_export, 0, Qt.AlignLeft)
        actions.addWidget(self.btn_policy, 0, Qt.AlignLeft)
        actions.addWidget(self.btn_manage, 0, Qt.AlignLeft)
        actions.addStretch(1)
        card.body.addLayout(actions)

        footer = QLabel(f"Več na {WEBSITE_LABEL}")
        footer.setObjectName("DashboardMuted")
        card.body.addWidget(footer)

        root.addWidget(card)

    def _export_placeholder(self) -> None:
        toast(self, "Izvoz podatkov bo na voljo kmalu.")

    def _open_policy(self) -> None:
        local = privacy_policy_path()
        if local is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(local.resolve())))
            toast(self, "Odpiram politiko zasebnosti…")
            return
        url = PRIVACY_POLICY_URL or WEBSITE_URL
        QDesktopServices.openUrl(QUrl(url))
        toast(self, "Odpiram politiko zasebnosti…")

    def _manage_placeholder(self) -> None:
        toast(
            self,
            "Upravljanje podatkov: uporabite Varnostne kopije ali se obrnite na podporo.",
        )
