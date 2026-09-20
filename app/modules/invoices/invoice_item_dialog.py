from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.article_repository import article_repository
from app.utils.vat import company_vat_liable, parse_vat_liable
from app.widgets.cards.enterprise_card import EnterpriseCard


class InvoiceItemDialog(EnterpriseDialog):

    def __init__(self, parent=None, vat_liable=None):
        super().__init__(
            parent,
            title="Dodaj postavko",
            heading="Dodaj postavko",
            size="SMALL",
            state_key="dialog.invoice_item",
        )
        self.article_id = None
        # Never use bare bool(): bool("NE")/bool("0") are True and would charge VAT.
        self.vat_liable = (
            company_vat_liable() if vat_liable is None else parse_vat_liable(vat_liable)
        )
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
        self.discount = QDoubleSpinBox()
        self.discount.setDecimals(2)
        self.discount.setRange(0, 100)
        self.discount.setSuffix(" %")
        self.vat = QDoubleSpinBox()
        self.vat.setDecimals(2)
        self.vat.setMaximum(100)
        self.total = QLabel("0.00 €")
        self.total.setObjectName("TotalValue")

        grid.add("Artikel", self.article, "Količina", self.quantity)
        grid.add("Cena", self.price, "Popust %", self.discount)
        grid.add("DDV %", self.vat)
        grid.add_full("Skupaj", self.total)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        if not self.vat_liable:
            self.vat.setValue(0)
            self.vat.setEnabled(False)

        self.article.currentIndexChanged.connect(self.article_changed)
        self.quantity.valueChanged.connect(self.calculate)
        self.price.valueChanged.connect(self.calculate)
        self.discount.valueChanged.connect(self.calculate)
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
        if self.vat_liable:
            self.vat.setValue(float(article[5]))
        else:
            self.vat.setValue(0)
        self.calculate()

    def calculate(self):
        from app.utils.money import format_eur, line_gross

        total = line_gross(
            self.quantity.value(),
            self.price.value(),
            self.vat.value(),
            self.discount.value(),
            vat_liable=self.vat_liable,
        )
        self.total.setText(format_eur(total))

    def get_data(self):
        from app.utils.money import as_float, line_gross

        article = self.article.currentData()
        discount = self.discount.value()
        vat = 0 if not self.vat_liable else self.vat.value()
        total = line_gross(
            self.quantity.value(),
            self.price.value(),
            vat,
            discount,
            vat_liable=self.vat_liable,
        )
        return [
            article[1],
            article[2],
            self.quantity.value(),
            article[3],
            self.price.value(),
            discount,
            vat,
            as_float(total),
            article[0],
        ]
