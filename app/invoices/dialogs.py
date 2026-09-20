from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QLineEdit, QMessageBox, QTextEdit, QVBoxLayout,
)


class InvoiceDatesDialog(QDialog):
    def __init__(self, parent=None, payment_terms_days=15):
        super().__init__(parent)
        self.setWindowTitle("Pretvori ponudbo v račun")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.issue_date = QDateEdit(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("dd.MM.yyyy")
        self.due_date = QDateEdit(
            QDate.currentDate().addDays(int(payment_terms_days))
        )
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Datum izdaje:", self.issue_date)
        form.addRow("Datum zapadlosti:", self.due_date)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        if self.due_date.date() < self.issue_date.date():
            QMessageBox.warning(
                self, "Neveljavni datumi",
                "Datum zapadlosti ne sme biti pred datumom izdaje.",
            )
            return
        self.accept()

    def get_data(self):
        return (
            self.issue_date.date().toString("yyyy-MM-dd"),
            self.due_date.date().toString("yyyy-MM-dd"),
        )


class PaymentDialog(QDialog):
    def __init__(self, remaining, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zabeleži plačilo")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.payment_date = QDateEdit(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("dd.MM.yyyy")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, max(float(remaining), 0.01))
        self.amount.setDecimals(2)
        self.amount.setValue(float(remaining))
        self.amount.setSuffix(" €")
        self.method = QComboBox()
        self.method.addItems(["Bančno nakazilo", "Gotovina", "Kartica", "Drugo"])
        self.reference = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(70)
        form.addRow("Datum:", self.payment_date)
        form.addRow("Znesek:", self.amount)
        form.addRow("Način:", self.method)
        form.addRow("Referenca:", self.reference)
        form.addRow("Opombe:", self.notes)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "amount": self.amount.value(), "method": self.method.currentText(),
            "reference": self.reference.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }
