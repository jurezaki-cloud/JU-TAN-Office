from PySide6.QtWidgets import QComboBox, QLineEdit, QTextEdit, QWidget

from app.core.ui.form_grid import FormGrid

COUNTRIES = (
    "Slovenija",
    "Avstrija",
    "Hrvaška",
    "Italija",
    "Nemčija",
    "Madžarska",
    "Švica",
)


class CustomerForm(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomerForm")

        self.company = QLineEdit()
        self.contact = QLineEdit()
        self.address = QTextEdit()
        self.address.setAcceptRichText(False)
        self.address.setMinimumHeight(72)
        self.address.setMaximumHeight(120)
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.country = QComboBox()
        self.country.setEditable(True)
        self.country.addItems(COUNTRIES)
        self.tax_number = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()

        self.company.setPlaceholderText("Naziv podjetja")
        self.contact.setPlaceholderText("Kontaktna oseba")
        self.address.setPlaceholderText("Ulica in hišna številka")
        self.postal_code.setPlaceholderText("1000")
        self.city.setPlaceholderText("Ljubljana")
        self.email.setPlaceholderText("info@podjetje.si")
        self.phone.setPlaceholderText("+386 ...")

        grid = FormGrid()
        grid.add("Podjetje", self.company, "Kontakt", self.contact)
        grid.add_full("Naslov", self.address)
        grid.add("Poštna št.", self.postal_code, "Kraj", self.city)
        grid.add("Država", self.country, "Davčna št.", self.tax_number)
        grid.add("E-pošta", self.email, "Telefon", self.phone)
        grid.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid.layout)

    def load(self, customer: dict | None) -> None:
        if not customer:
            self.country.setCurrentText("Slovenija")
            return

        self.company.setText(customer.get("company", ""))
        self.contact.setText(customer.get("contact", ""))
        self.address.setPlainText(customer.get("address", ""))
        self.postal_code.setText(customer.get("postal_code", ""))
        self.city.setText(customer.get("city", ""))
        country = customer.get("country", "") or "Slovenija"
        if self.country.findText(country) < 0:
            self.country.addItem(country)
        self.country.setCurrentText(country)
        self.tax_number.setText(customer.get("tax_number", ""))
        self.email.setText(customer.get("email", ""))
        self.phone.setText(customer.get("phone", ""))

    def get_data(self) -> dict:
        return {
            "company": self.company.text().strip(),
            "contact": self.contact.text().strip(),
            "address": self.address.toPlainText().strip(),
            "postal_code": self.postal_code.text().strip(),
            "city": self.city.text().strip(),
            "country": self.country.currentText().strip(),
            "tax_number": self.tax_number.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
        }
