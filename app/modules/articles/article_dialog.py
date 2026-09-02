from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QDoubleSpinBox,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from app.database.article_repository import article_repository


class ArticleDialog(QDialog):

    def __init__(self, parent=None, article=None):
        super().__init__(parent)

        self.article = article

        self.setWindowTitle(
            "Uredi artikel" if article else "Nov artikel"
        )

        self.resize(520, 520)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Šifra
        self.code = QLineEdit()

        if article is None:
            self.code.setText(article_repository.get_next_code())

        # Naziv
        self.name = QLineEdit()

        # Opis
        self.description = QTextEdit()
        self.description.setFixedHeight(90)

        # Enota
        self.unit = QComboBox()
        self.unit.addItems([
            "kos",
            "ura",
            "dan",
            "m",
            "m²",
            "m³",
            "kg",
            "paket",
            "komplet",
            "storitev",
        ])

        # Cena
        self.price = QDoubleSpinBox()
        self.price.setMaximum(999999999)
        self.price.setDecimals(2)
        self.price.setSuffix(" €")

        # DDV
        self.vat = QComboBox()
        self.vat.addItems([
            "22",
            "9.5",
            "5",
            "0",
        ])

        form.addRow("Šifra:", self.code)
        form.addRow("Naziv:", self.name)
        form.addRow("Opis:", self.description)
        form.addRow("Enota:", self.unit)
        form.addRow("Cena:", self.price)
        form.addRow("DDV:", self.vat)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.btn_cancel = QPushButton("Prekliči")
        self.btn_save = QPushButton("Shrani")

        buttons.addStretch()
        buttons.addWidget(self.btn_cancel)
        buttons.addWidget(self.btn_save)

        layout.addLayout(buttons)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_accept)

        if article:
            self.load_article(article)

    def load_article(self, article):

        self.code.setText(article.get("code", ""))
        self.name.setText(article.get("name", ""))
        self.description.setPlainText(
            article.get("description", "")
        )

        unit = article.get("unit", "kos")
        idx = self.unit.findText(unit)

        if idx >= 0:
            self.unit.setCurrentIndex(idx)

        self.price.setValue(float(article.get("price", 0)))

        vat = str(article.get("vat", "22"))
        idx = self.vat.findText(vat)

        if idx >= 0:
            self.vat.setCurrentIndex(idx)

    def validate_and_accept(self):

        if not self.code.text().strip():
            QMessageBox.warning(
                self,
                "Napaka",
                "Šifra artikla je obvezna.",
            )
            return

        if not self.name.text().strip():
            QMessageBox.warning(
                self,
                "Napaka",
                "Naziv artikla je obvezen.",
            )
            return

        self.accept()

    def get_data(self):

        return {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "description": self.description.toPlainText().strip(),
            "unit": self.unit.currentText(),
            "price": self.price.value(),
            "vat": float(self.vat.currentText()),
        }