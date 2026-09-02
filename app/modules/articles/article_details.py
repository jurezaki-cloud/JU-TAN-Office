from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QPushButton,
)


class ArticleDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.article_id = None

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.code = QLabel("-")
        self.name = QLabel("-")
        self.description = QLabel("-")
        self.unit = QLabel("-")
        self.price = QLabel("-")
        self.vat = QLabel("-")

        form.addRow("Šifra:", self.code)
        form.addRow("Naziv:", self.name)
        form.addRow("Opis:", self.description)
        form.addRow("Enota:", self.unit)
        form.addRow("Cena:", self.price)
        form.addRow("DDV:", self.vat)

        layout.addLayout(form)

        self.editButton = QPushButton("Uredi artikel")
        layout.addWidget(self.editButton)

        layout.addStretch()

    def load_article(self, row):

        if row is None:
            return

        self.article_id = row[0]

        self.code.setText(str(row[1]))
        self.name.setText(str(row[2]))
        self.description.setText(str(row[3]))
        self.unit.setText(str(row[4]))
        self.price.setText(f"{float(row[5]):.2f} €")
        self.vat.setText(f"{float(row[6]):.0f} %")