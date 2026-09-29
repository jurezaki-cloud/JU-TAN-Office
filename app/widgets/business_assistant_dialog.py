"""Read-only business assistant dialog."""
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QVBoxLayout,
)

from app.services.business_assistant import answer

EXAMPLES = (
    "Kdo mi dolguje več kot 500 €?",
    "Katere ponudbe čakajo več kot 14 dni?",
    "Kateri artikli imajo nizko zalogo?",
    "Povzetek poslovanja danes",
    "Povzetek poslovanja ta teden",
    "Povzetek poslovanja ta mesec",
)


class BusinessAssistantDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JU-TAN pomočnik")
        self.resize(610, 440)
        layout = QVBoxLayout(self)
        intro = QLabel("Lokalni vpogled v tvoje podatke. Odgovori ne spreminjajo zapisov.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.examples = QComboBox()
        self.examples.addItem("Izberi primer vprašanja…")
        self.examples.addItems(EXAMPLES)
        self.examples.activated.connect(self._example)
        layout.addWidget(self.examples)
        row = QHBoxLayout()
        self.question = QLineEdit()
        self.question.setPlaceholderText("Vpiši poslovno vprašanje…")
        self.question.returnPressed.connect(self.ask)
        row.addWidget(self.question, 1)
        ask_button = QPushButton("Vprašaj")
        ask_button.clicked.connect(self.ask)
        row.addWidget(ask_button)
        layout.addLayout(row)
        self.title = QLabel("Odgovor")
        layout.addWidget(self.title)
        self.response = QTextEdit()
        self.response.setReadOnly(True)
        layout.addWidget(self.response, 1)
        self.question.setFocus()

    def _example(self, index: int) -> None:
        if index > 0:
            self.question.setText(EXAMPLES[index - 1])
            self.ask()

    def ask(self) -> None:
        try:
            result = answer(self.question.text())
        except Exception:
            from app.core.logger import logger
            logger.exception("Business assistant query failed")
            self.title.setText("Napaka pri branju podatkov")
            self.response.setPlainText("Preveri povezavo z bazo in poskusi znova.")
            return
        self.title.setText(result.title)
        self.response.setPlainText(result.body)
