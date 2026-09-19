from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.vat import vat_liable_label
from app.widgets.cards.enterprise_card import EnterpriseCard


class CompanyCard(QWidget):
    save_clicked = Signal()
    reset_clicked = Signal()
    logo_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.logo_path = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Profil podjetja")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name = QLineEdit()
        self.address = QLineEdit()
        self.postal = QLineEdit()
        self.city = QLineEdit()
        self.country = QLineEdit()
        self.phone = QLineEdit()
        self.mobile = QLineEdit()
        self.email = QLineEdit()
        self.website = QLineEdit()
        self.tax = QLineEdit()
        self.registration = QLineEdit()
        self.iban = QLineEdit()
        self.swift = QLineEdit()
        self.vat_liable = QComboBox()
        self.vat_liable.addItems(["DA", "NE"])
        self.vat_liable.setCurrentText("DA")

        form.addRow("Naziv podjetja", self.name)
        form.addRow("Naslov", self.address)
        form.addRow("Poštna številka", self.postal)
        form.addRow("Kraj", self.city)
        form.addRow("Država", self.country)
        form.addRow("Telefon", self.phone)
        form.addRow("GSM", self.mobile)
        form.addRow("Email", self.email)
        form.addRow("Spletna stran", self.website)
        form.addRow("Davčna številka", self.tax)
        form.addRow("Matična številka", self.registration)
        form.addRow("IBAN", self.iban)
        form.addRow("SWIFT", self.swift)
        form.addRow("Zavezanec za DDV", self.vat_liable)
        card.body.addLayout(form)

        vat_hint = QLabel(
            "Izbira se shrani takoj. Ob NE novi računi, ponudbe in naročila ne obračunajo DDV "
            "ter vključijo obvestilo po 94. členu ZDDV-1. Obstoječi dokumenti ostanejo nespremenjeni."
        )
        vat_hint.setObjectName("DashboardMuted")
        vat_hint.setWordWrap(True)
        card.body.addWidget(vat_hint)

        self.logo_label = QLabel("Logotip ni izbran")
        self.logo_label.setObjectName("LogoPreview")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(90, 90)
        card.body.addWidget(self.logo_label)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(8)
        self.btn_logo = QPushButton("Izberi logotip")
        self.btn_logo.setObjectName("SecondaryButton")
        self.btn_clear_logo = QPushButton("Odstrani")
        self.btn_clear_logo.setObjectName("SecondaryButton")
        for button in (self.btn_logo, self.btn_clear_logo):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            logo_row.addWidget(button)
        logo_row.addStretch()
        card.body.addLayout(logo_row)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.btn_save = QPushButton("Shrani")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_reset = QPushButton("Ponastavi")
        self.btn_reset.setObjectName("SecondaryButton")
        for button in (self.btn_reset, self.btn_save):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
        actions.addStretch()
        actions.addWidget(self.btn_reset)
        actions.addWidget(self.btn_save)
        card.body.addLayout(actions)

        layout.addWidget(card)

        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_reset.clicked.connect(self.reset_clicked.emit)
        self.btn_logo.clicked.connect(self._pick_logo)
        self.btn_clear_logo.clicked.connect(self._clear_logo)
        self.vat_liable.currentTextChanged.connect(self._persist_vat_liable)

    def values(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "address": self.address.text().strip(),
            "postal_code": self.postal.text().strip(),
            "city": self.city.text().strip(),
            "country": self.country.text().strip(),
            "phone": self.phone.text().strip(),
            "mobile": self.mobile.text().strip(),
            "email": self.email.text().strip(),
            "website": self.website.text().strip(),
            "tax_number": self.tax.text().strip(),
            "registration_number": self.registration.text().strip(),
            "iban": self.iban.text().strip(),
            "swift": self.swift.text().strip(),
            "logo": self.logo_path,
            "vat_liable": self.vat_liable.currentText(),
        }

    def set_values(self, company, swift: str = "") -> None:
        if not company:
            return
        self.name.setText(company[1] or "")
        self.address.setText(company[3] or "")
        self.postal.setText(company[4] or "")
        self.city.setText(company[5] or "")
        self.country.setText(company[6] or "")
        self.tax.setText(company[7] or "")
        self.registration.setText(company[8] or "")
        self.iban.setText(company[9] or "")
        self.email.setText(company[11] or "")
        self.website.setText(company[12] or "")
        self.phone.setText(company[13] or "")
        self.mobile.setText(company[14] or "")
        self.swift.setText(swift or "")
        self.set_logo(company[15] or "")
        liable = company[22] if len(company) > 22 else 1
        self.vat_liable.blockSignals(True)
        self.vat_liable.setCurrentText(vat_liable_label(liable))
        self.vat_liable.blockSignals(False)

    def _persist_vat_liable(self, text: str = "") -> None:
        """Write Zavezanec za DDV immediately so new documents match the visible UI."""
        from app.core.permissions import can
        from app.database.company_repository import company_repository

        if not can("settings"):
            return
        value = text or self.vat_liable.currentText()
        company_repository.set_vat_liable(value)

    def set_logo(self, path: str) -> None:
        self.logo_path = path or ""
        if self.logo_path and Path(self.logo_path).exists():
            pixmap = QPixmap(self.logo_path)
            self.logo_label.setPixmap(pixmap.scaled(
                90,
                90,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            ))
            self.logo_label.setText("")
        else:
            self.logo_label.setPixmap(QPixmap())
            self.logo_label.setText("Logotip ni izbran")

    def _pick_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Izberi logotip",
            "",
            "Slike (*.png *.jpg *.jpeg *.svg *.webp)",
        )
        if path:
            self.set_logo(path)
            self.logo_changed.emit(path)

    def _clear_logo(self):
        self.set_logo("")
        self.logo_changed.emit("")
