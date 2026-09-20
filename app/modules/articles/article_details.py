from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QPushButton,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class ArticleDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.article_id = None
        self.setObjectName("ArticleDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti artikla")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.code = QLabel("-")
        self.name = QLabel("-")
        self.description = QLabel("-")
        self.unit = QLabel("-")
        self.price = QLabel("-")
        self.vat = QLabel("-")

        for label in (
            self.code,
            self.name,
            self.description,
            self.unit,
            self.price,
            self.vat,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Šifra", self.code)
        form.addRow("Naziv", self.name)
        form.addRow("Opis", self.description)
        form.addRow("Enota", self.unit)
        form.addRow("Cena", self.price)
        form.addRow("DDV", self.vat)
        card.body.addLayout(form)

        self.editButton = QPushButton("Uredi artikel")
        self.editButton.setObjectName("SecondaryButton")
        self.editButton.setMinimumHeight(36)
        card.body.addWidget(self.editButton)
        card.body.addStretch()

        layout.addWidget(card)

    def clear(self):
        self.article_id = None
        self.code.setText("-")
        self.name.setText("-")
        self.description.setText("-")
        self.unit.setText("-")
        self.price.setText("-")
        self.vat.setText("-")

    def load_article(self, row):

        if row is None:
            self.clear()
            return

        self.article_id = row[0]

        self.code.setText(str(row[1]))
        self.name.setText(str(row[2]))
        self.description.setText(str(row[3]))
        self.unit.setText(str(row[4]))
        self.price.setText(f"{float(row[5]):.2f} €")
        self.vat.setText(f"{float(row[6]):.0f} %")
