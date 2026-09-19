from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from app.core.ui.notify import toast
from app.core.ui.form_grid import FormGrid
from app.core.ui.sizes import FOOTER_HEIGHT, LAYOUT_SPACING, OUTER_MARGIN
from app.core.ui.window_state import remember_layout
from app.database.company_repository import company_repository


class CompanyPage(QWidget):

    def __init__(self):
        super().__init__()

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

        title = QLabel("Podatki podjetja")
        title.setObjectName("PageTitle")
        title.hide()
        body.addWidget(title)

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
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)

        grid = FormGrid()
        grid.add("Naziv", self.name, "Pravni naziv", self.legal_name)
        grid.add("Naslov", self.address, "Poštna št.", self.postal)
        grid.add("Kraj", self.city, "Država", self.country)
        grid.add("Davčna št.", self.tax, "Matična št.", self.registration)
        grid.add("IBAN", self.iban, "Banka", self.bank)
        grid.add("Telefon", self.phone, "Mobilni", self.mobile)
        grid.add("Email", self.email, "Spletna stran", self.website)
        grid.add_full("Opombe", self.notes)
        body.addLayout(grid.layout)
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
        footer_layout.addWidget(self.save_btn)
        root.addWidget(footer)

        self.save_btn.clicked.connect(self.save)
        remember_layout(self, "page.company")
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
            "",
            "RAC",
            "PON",
            1,
            1,
            22,
            self.notes.toPlainText(),
        )
        audit("edit", "company")

        toast(self, "Podatki podjetja so shranjeni")
