from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from app.core.validation import required_text
from app.services.offer_calculation import calculate_item


class OfferItemDialog(QDialog):
    def __init__(self, articles, parent=None, item=None):
        super().__init__(parent)
        self.articles = articles
        self.setWindowTitle("Uredi postavko" if item else "Nova postavka")
        self.resize(500, 520)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.article = QComboBox()
        self.article.addItem("Ročni vnos", None)
        for row in articles:
            self.article.addItem(f"{row[1]} – {row[2]}", row[0])
        self.code = QLineEdit()
        self.name = QLineEdit()
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0.001, 999999999)
        self.quantity.setDecimals(3)
        self.quantity.setValue(1)
        self.unit = QComboBox()
        self.unit.setEditable(True)
        self.unit.addItems(["kos", "ura", "dan", "m", "m²", "m³", "kg", "storitev"])
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 999999999)
        self.price.setDecimals(2)
        self.price.setSuffix(" €")
        self.discount = QDoubleSpinBox()
        self.discount.setRange(0, 100)
        self.discount.setDecimals(2)
        self.discount.setSuffix(" %")
        self.vat = QComboBox()
        self.vat.setEditable(True)
        self.vat.addItems(["22", "9.5", "5", "0"])

        for label, widget in (
            ("Artikel:", self.article), ("Šifra:", self.code),
            ("Naziv:", self.name), ("Opis:", self.description),
            ("Količina:", self.quantity), ("Enota:", self.unit),
            ("Cena brez DDV:", self.price), ("Popust:", self.discount),
            ("DDV:", self.vat),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.article.currentIndexChanged.connect(self.load_selected_article)

        if item:
            self.load_item(item)

    def load_selected_article(self):
        article_id = self.article.currentData()
        if article_id is None:
            return
        article = next((row for row in self.articles if row[0] == article_id), None)
        if article:
            self.code.setText(article[1] or "")
            self.name.setText(article[2] or "")
            self.unit.setCurrentText(article[3] or "kos")
            self.price.setValue(float(article[4] or 0))
            self.vat.setCurrentText(str(article[5] or 0))

    def load_item(self, item):
        index = self.article.findData(item.get("article_id"))
        self.article.setCurrentIndex(max(index, 0))
        self.code.setText(item.get("code", ""))
        self.name.setText(item.get("name", ""))
        self.description.setPlainText(item.get("description", ""))
        self.quantity.setValue(float(item.get("quantity", 1)))
        self.unit.setCurrentText(item.get("unit", "kos"))
        self.price.setValue(float(item.get("price", 0)))
        self.discount.setValue(float(item.get("discount", 0)))
        self.vat.setCurrentText(str(item.get("vat", 22)))

    def validate_and_accept(self):
        try:
            required_text(self.name.text(), "Naziv")
            required_text(self.unit.currentText(), "Enota")
            calculate_item(self.get_data())
        except ValueError as error:
            QMessageBox.warning(self, "Neveljavna postavka", str(error))
            return
        self.accept()

    def get_data(self):
        return {
            "article_id": self.article.currentData(),
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "description": self.description.toPlainText().strip(),
            "quantity": self.quantity.value(),
            "unit": self.unit.currentText().strip(),
            "price": self.price.value(),
            "discount": self.discount.value(),
            "vat": float(self.vat.currentText().replace(",", ".") or 0),
        }
