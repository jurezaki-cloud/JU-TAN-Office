from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.article_repository import article_repository
from app.widgets.cards.enterprise_card import EnterpriseCard


class ArticleDialog(EnterpriseDialog):

    def __init__(self, parent=None, article=None):
        title = "Uredi artikel" if article else "Nov artikel"
        super().__init__(parent, title=title, heading=title, size="SMALL", state_key="dialog.article")
        self.article = article
        self.setObjectName("ArticleDialog")
        self.bind_save(self.validate_and_accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()

        self.code = QLineEdit()
        if article is None:
            self.code.setText(article_repository.get_next_code())
        self.name = QLineEdit()
        self.description = QTextEdit()
        self.description.setAcceptRichText(False)
        self.description.setMinimumHeight(72)
        self.description.setMaximumHeight(120)
        self.unit = QComboBox()
        self.unit.addItems([
            "kos", "ura", "dan", "m", "m²", "m³", "kg", "paket", "komplet", "storitev",
        ])
        self.price = QDoubleSpinBox()
        self.price.setMaximum(999999999)
        self.price.setDecimals(2)
        self.price.setSuffix(" €")
        self.vat = QComboBox()
        self.vat.addItems(["22", "9.5", "5", "0"])

        grid.add("Šifra", self.code, "Naziv", self.name)
        grid.add_full("Opis", self.description)
        grid.add("Enota", self.unit, "Cena", self.price)
        grid.add("DDV", self.vat)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

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
