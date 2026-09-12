from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.article_repository import article_repository
from app.widgets.cards.enterprise_card import EnterpriseCard


class InvoiceItemDialog(EnterpriseDialog):

    def __init__(self, parent=None):
        super().__init__(
            parent,
            title="Dodaj postavko",
            heading="Dodaj postavko",
            size="SMALL",
            state_key="dialog.invoice_item",
        )
        self.article_id = None
        self.setObjectName("InvoiceItemDialog")

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()

        self.article = QComboBox()
        self.quantity = QDoubleSpinBox()
        self.quantity.setDecimals(2)
        self.quantity.setMaximum(999999)
        self.quantity.setValue(1)
        self.price = QDoubleSpinBox()
        self.price.setDecimals(2)
        self.price.setMaximum(9999999)
        self.vat = QDoubleSpinBox()
        self.vat.setDecimals(2)
        self.vat.setMaximum(100)
        self.total = QLabel("0.00 €")
        self.total.setObjectName("TotalValue")

        grid.add("Artikel", self.article, "Količina", self.quantity)
        grid.add("Cena", self.price, "DDV %", self.vat)
        grid.add_full("Skupaj", self.total)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        self.article.currentIndexChanged.connect(self.article_changed)
        self.quantity.valueChanged.connect(self.calculate)
        self.price.valueChanged.connect(self.calculate)
        self.vat.valueChanged.connect(self.calculate)
        self.load_articles()

    def load_articles(self):
        self.article.clear()
        articles = article_repository.get_all()
        for article in articles:
            self.article.addItem(f"{article[1]} - {article[2]}", article)
        if self.article.count():
            self.article.setCurrentIndex(0)
            self.article_changed()

    def article_changed(self):
        article = self.article.currentData()
        if article is None:
            return
        self.article_id = article[0]
        self.price.setValue(float(article[4]))
        self.vat.setValue(float(article[5]))
        self.calculate()

    def calculate(self):
        subtotal = self.quantity.value() * self.price.value()
        total = subtotal * (1 + self.vat.value() / 100)
        self.total.setText(f"{total:.2f} €")

    def get_data(self):
        article = self.article.currentData()
        subtotal = self.quantity.value() * self.price.value()
        total = subtotal * (1 + self.vat.value() / 100)
        return [
            article[1],
            article[2],
            self.quantity.value(),
            article[3],
            self.price.value(),
            self.vat.value(),
            round(total, 2),
            article[0],
        ]
