from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.brand_icons import brand_icon
from app.core.ui.notify import toast
from app.core.ui.form_grid import FormGrid
from app.core.ui.sizes import FOOTER_HEIGHT, LAYOUT_SPACING, OUTER_MARGIN
from app.core.ui.window_state import remember_layout
from app.database.company_repository import company_repository
from app.utils.vat import vat_liable_int, vat_liable_label
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.common.page_chrome import PageHeader


class CompanyPage(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("CompanyPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("DialogScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN)
        body.setSpacing(LAYOUT_SPACING)

        header = PageHeader(
            "Podjetje",
            "Podatki se uporabljajo na dokumentih in v PDF izvozu.",
        )
        body.addWidget(header)

        self.name = QLineEdit()
        self.legal_name = QLineEdit()
        self.address = QLineEdit()
        self.postal = QLineEdit()
        self.city = QLineEdit()
        self.country = QLineEdit()
        self.tax = QLineEdit()
        self.registration = QLineEdit()
        self.iban = QLineEdit()
        self.bank = QLineEdit()
        self.phone = QLineEdit()
        self.mobile = QLineEdit()
        self.email = QLineEdit()
        self.website = QLineEdit()
        self.vat_liable = QComboBox()
        self.vat_liable.addItems(["DA", "NE"])
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)

        identity = EnterpriseCard("DashboardCard")
        identity_title = QLabel("Identiteta")
        identity_title.setObjectName("SectionTitle")
        identity.body.addWidget(identity_title)
        identity_grid = FormGrid()
        identity_grid.add("Naziv", self.name, "Pravni naziv", self.legal_name)
        identity_grid.add("Naslov", self.address, "Poštna št.", self.postal)
        identity_grid.add("Kraj", self.city, "Država", self.country)
        identity.body.addLayout(identity_grid.layout)
        body.addWidget(identity)

        tax_card = EnterpriseCard("DashboardCard")
        tax_title = QLabel("Davčni in bančni podatki")
        tax_title.setObjectName("SectionTitle")
        tax_card.body.addWidget(tax_title)
        tax_grid = FormGrid()
        tax_grid.add("Davčna št.", self.tax, "Matična št.", self.registration)
        tax_grid.add("IBAN", self.iban, "Banka", self.bank)
        tax_grid.add("Zavezanec za DDV", self.vat_liable)
        tax_card.body.addLayout(tax_grid.layout)
        body.addWidget(tax_card)

        contact = EnterpriseCard("DashboardCard")
        contact_title = QLabel("Kontakt")
        contact_title.setObjectName("SectionTitle")
        contact.body.addWidget(contact_title)
        contact_grid = FormGrid()
        contact_grid.add("Telefon", self.phone, "Mobilni", self.mobile)
        contact_grid.add("Email", self.email, "Spletna stran", self.website)
        contact_grid.add_full("Opombe", self.notes)
        contact.body.addLayout(contact_grid.layout)
        body.addWidget(contact)
        body.addStretch()

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        footer = QWidget()
        footer.setObjectName("DialogFooter")
        footer.setFixedHeight(FOOTER_HEIGHT)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(OUTER_MARGIN, 0, OUTER_MARGIN, 0)
        footer_layout.addStretch()
        self.save_btn = QPushButton("Shrani")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setIcon(brand_icon("save", color="#FFFFFF", size=14))
        footer_layout.addWidget(self.save_btn)
        root.addWidget(footer)

        self.save_btn.clicked.connect(self.save)
        self.vat_liable.currentTextChanged.connect(self._persist_vat_liable)
        remember_layout(self, "page.company")
        self._logo = ""
        self._invoice_prefix = "RAC"
        self._offer_prefix = "PON"
        self._invoice_counter = 1
        self._offer_counter = 1
        self._default_vat = 22
        self.load()

    def load(self):

        company = company_repository.get_company()

        if not company:
            return

        (
            _,
            name,
            legal_name,
            address,
            postal,
            city,
            country,
            tax,
            registration,
            iban,
            bank,
            email,
            website,
            phone,
            mobile,
            logo,
            invoice_prefix,
            offer_prefix,
            invoice_counter,
            offer_counter,
            default_vat,
            notes,
            *rest,
        ) = company

        self.name.setText(name or "")
        self.legal_name.setText(legal_name or "")
        self.address.setText(address or "")
        self.postal.setText(postal or "")
        self.city.setText(city or "")
        self.country.setText(country or "")
        self.tax.setText(tax or "")
        self.registration.setText(registration or "")
        self.iban.setText(iban or "")
        self.bank.setText(bank or "")
        self.phone.setText(phone or "")
        self.mobile.setText(mobile or "")
        self.email.setText(email or "")
        self.website.setText(website or "")
        self.notes.setPlainText(notes or "")
        self._logo = logo or ""
        self._invoice_prefix = invoice_prefix or "RAC"
        self._offer_prefix = offer_prefix or "PON"
        self._invoice_counter = int(invoice_counter or 1)
        self._offer_counter = int(offer_counter or 1)
        self._default_vat = float(default_vat if default_vat is not None else 22)
        liable = rest[0] if rest else 1
        self.vat_liable.blockSignals(True)
        self.vat_liable.setCurrentText(vat_liable_label(liable))
        self.vat_liable.blockSignals(False)

    def _persist_vat_liable(self, text: str = "") -> None:
        from app.core.permissions import can
        from app.database.company_repository import company_repository

        if not can("settings"):
            return
        company_repository.set_vat_liable(text or self.vat_liable.currentText())

    def save(self):
        from app.core.permissions import allow, audit

        if not allow("settings", self):
            return

        company_repository.save(
            self.name.text(),
            self.legal_name.text(),
            self.address.text(),
            self.postal.text(),
            self.city.text(),
            self.country.text(),
            self.tax.text(),
            self.registration.text(),
            self.iban.text(),
            self.bank.text(),
            self.email.text(),
            self.website.text(),
            self.phone.text(),
            self.mobile.text(),
            self._logo,
            self._invoice_prefix,
            self._offer_prefix,
            self._invoice_counter,
            self._offer_counter,
            self._default_vat,
            self.notes.toPlainText(),
            vat_liable_int(self.vat_liable.currentText()),
        )
        audit("edit", "company")

        toast(self, "Podatki podjetja so shranjeni")
