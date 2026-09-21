"""About card — JU-TAN branding, version, company and support."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.utils.vat import WEBSITE_LABEL, WEBSITE_URL
from app.widgets.cards.enterprise_card import EnterpriseCard

SUPPORT_EMAIL = "support@ju-tan.com"


class _AboutTile(QFrame):
    def __init__(self, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("LicenseMetaTile")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.caption = QLabel(caption)
        self.caption.setObjectName("LicenseMetaCaption")
        self.value = QLabel("—")
        self.value.setObjectName("LicenseMetaValue")
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.value.setWordWrap(True)

        layout.addWidget(self.caption)
        layout.addWidget(self.value)


class AboutCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        card.body.setContentsMargins(22, 22, 22, 22)
        card.body.setSpacing(16)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        brand_col = QVBoxLayout()
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(4)

        eyebrow = QLabel("JU-TAN")
        eyebrow.setObjectName("LicenseEyebrow")

        self.app_name = QLabel("JU-TAN Office")
        self.app_name.setObjectName("LicenseCardTitle")

        self.edition = QLabel("Enterprise Edition")
        self.edition.setObjectName("DashboardMuted")
        self.edition.setWordWrap(True)

        brand_col.addWidget(eyebrow)
        brand_col.addWidget(self.app_name)
        brand_col.addWidget(self.edition)
        header.addLayout(brand_col, 1)
        card.body.addLayout(header)

        hero = QFrame()
        hero.setObjectName("LicenseHero")
        hero.setAttribute(Qt.WA_StyledBackground, True)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(4)

        company_caption = QLabel("Podjetje")
        company_caption.setObjectName("LicenseMetaCaption")
        self.lbl_company = QLabel("JU-TAN Studio")
        self.lbl_company.setObjectName("LicenseCompanyName")
        self.lbl_company.setWordWrap(True)

        support_caption = QLabel("Podpora")
        support_caption.setObjectName("LicenseMetaCaption")
        self.lbl_support = QLabel(SUPPORT_EMAIL)
        self.lbl_support.setObjectName("LicenseMetaValue")
        self.lbl_support.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_website = QLabel(WEBSITE_LABEL)
        self.lbl_website.setObjectName("DashboardMuted")

        hero_layout.addWidget(company_caption)
        hero_layout.addWidget(self.lbl_company)
        hero_layout.addSpacing(8)
        hero_layout.addWidget(support_caption)
        hero_layout.addWidget(self.lbl_support)
        hero_layout.addWidget(self.lbl_website)
        card.body.addWidget(hero)

        meta = QWidget()
        grid = QGridLayout(meta)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self._tile_version = _AboutTile("Verzija")
        self._tile_python = _AboutTile("Python")
        self._tile_qt = _AboutTile("Qt")
        self._tile_sqlite = _AboutTile("SQLite")
        self._tile_build = _AboutTile("Build")
        self._tile_copy = _AboutTile("Copyright")

        self.lbl_version = self._tile_version.value
        self.lbl_python = self._tile_python.value
        self.lbl_qt = self._tile_qt.value
        self.lbl_sqlite = self._tile_sqlite.value
        self.lbl_build = self._tile_build.value
        self.lbl_copy = self._tile_copy.value

        tiles = (
            self._tile_version,
            self._tile_python,
            self._tile_qt,
            self._tile_sqlite,
            self._tile_build,
            self._tile_copy,
        )
        for index, tile in enumerate(tiles):
            grid.addWidget(tile, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card.body.addWidget(meta)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        actions.setSpacing(10)

        self.btn_website = QPushButton("Odpri spletno stran")
        self.btn_website.setObjectName("SecondaryButton")
        self.btn_website.setCursor(Qt.PointingHandCursor)
        self.btn_website.setMinimumHeight(36)
        self.btn_website.clicked.connect(self._open_website)

        self.btn_support = QPushButton("Kontakt podpora")
        self.btn_support.setObjectName("SecondaryButton")
        self.btn_support.setCursor(Qt.PointingHandCursor)
        self.btn_support.setMinimumHeight(36)
        self.btn_support.clicked.connect(self._open_support)

        actions.addWidget(self.btn_website, 0, Qt.AlignLeft)
        actions.addWidget(self.btn_support, 0, Qt.AlignLeft)
        actions.addStretch(1)
        card.body.addLayout(actions)

        layout.addWidget(card)

    def set_values(self, info: dict) -> None:
        self.app_name.setText(info.get("app") or info.get("name") or "JU-TAN Office")
        self.edition.setText(info.get("edition", "Enterprise Edition"))
        self.lbl_company.setText(info.get("company") or "JU-TAN Studio")
        self.lbl_support.setText(info.get("support") or SUPPORT_EMAIL)
        self.lbl_website.setText(info.get("website") or WEBSITE_LABEL)
        self.lbl_version.setText(info.get("version", "—"))
        self.lbl_python.setText(info.get("python", "—"))
        self.lbl_qt.setText(info.get("qt", "—"))
        self.lbl_sqlite.setText(info.get("sqlite", "—"))
        self.lbl_build.setText(info.get("build", "—"))
        self.lbl_copy.setText(info.get("copyright", "—"))

    def _open_website(self) -> None:
        QDesktopServices.openUrl(QUrl(WEBSITE_URL if WEBSITE_URL.startswith("http") else f"https://{WEBSITE_LABEL}"))

    def _open_support(self) -> None:
        QDesktopServices.openUrl(QUrl(f"mailto:{SUPPORT_EMAIL}"))
