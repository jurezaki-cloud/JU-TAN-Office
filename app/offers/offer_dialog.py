from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)

from app.core.validation import required_text
from app.offers.offer_item_dialog import OfferItemDialog
from app.services.offer_calculation import calculate_offer


class OfferDialog(QDialog):
    def __init__(self, customers, articles, number, parent=None, offer=None, items=None):
        super().__init__(parent)
        self.offer = offer
        self.articles = articles
        self.items = list(items or [])
        self.setWindowTitle("Uredi ponudbo" if offer else "Nova ponudba")
        self.resize(1050, 720)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.number = QLabel(number)
        self.customer = QComboBox()
        for row in customers:
            self.customer.addItem(row[1], row[0])
        self.issue_date = QDateEdit(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("dd.MM.yyyy")
        self.valid_until = QDateEdit(QDate.currentDate().addDays(30))
        self.valid_until.setCalendarPopup(True)
        self.valid_until.setDisplayFormat("dd.MM.yyyy")
        self.status = QComboBox()
        self.status.addItems(["Osnutek", "Poslana", "Sprejeta", "Zavrnjena"])
        form.addRow("Številka:", self.number)
        form.addRow("Stranka:", self.customer)
        form.addRow("Datum izdaje:", self.issue_date)
        form.addRow("Velja do:", self.valid_until)
        form.addRow("Status:", self.status)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.btn_add = QPushButton("➕ Dodaj postavko")
        self.btn_edit = QPushButton("✏️ Uredi postavko")
        self.btn_remove = QPushButton("🗑 Odstrani postavko")
        actions.addWidget(self.btn_add)
        actions.addWidget(self.btn_edit)
        actions.addWidget(self.btn_remove)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Šifra", "Naziv", "Količina", "Enota", "Cena", "Popust",
            "DDV", "Skupaj",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        totals = QHBoxLayout()
        totals.addStretch()
        self.lbl_subtotal = QLabel()
        self.lbl_discount = QLabel()
        self.lbl_vat = QLabel()
        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-size:18px;font-weight:bold;")
        for label in (
            self.lbl_subtotal, self.lbl_discount, self.lbl_vat, self.lbl_total
        ):
            totals.addWidget(label)
        layout.addLayout(totals)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Opombe na ponudbi …")
        self.notes.setMaximumHeight(80)
        layout.addWidget(self.notes)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_remove.clicked.connect(self.remove_item)
        self.table.doubleClicked.connect(self.edit_item)

        if offer:
            self._load_offer(offer)
        self.refresh_items()

    def _load_offer(self, offer):
        customer_index = self.customer.findData(offer[2])
        if customer_index >= 0:
            self.customer.setCurrentIndex(customer_index)
        for widget, value in ((self.issue_date, offer[3]), (self.valid_until, offer[4])):
            date = QDate.fromString(value or "", "yyyy-MM-dd")
            if date.isValid():
                widget.setDate(date)
        status_index = self.status.findText(offer[5])
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)
        self.notes.setPlainText(offer[10] or "")

    def current_row(self):
        return self.table.currentRow()

    def add_item(self):
        dialog = OfferItemDialog(self.articles, self)
        if dialog.exec():
            self.items.append(dialog.get_data())
            self.refresh_items()

    def edit_item(self, *_):
        row = self.current_row()
        if row < 0:
            QMessageBox.information(self, "Postavka", "Najprej izberite postavko.")
            return
        dialog = OfferItemDialog(self.articles, self, self.items[row])
        if dialog.exec():
            self.items[row] = dialog.get_data()
            self.refresh_items()
            self.table.selectRow(row)

    def remove_item(self):
        row = self.current_row()
        if row < 0:
            QMessageBox.information(self, "Postavka", "Najprej izberite postavko.")
            return
        del self.items[row]
        self.refresh_items()

    def refresh_items(self):
        calculation = calculate_offer(self.items)
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(calculation["items"]):
            values = (
                item.get("code", ""), item.get("name", ""),
                f'{float(item.get("quantity", 0)):.3f}', item.get("unit", ""),
                f'{float(item.get("price", 0)):.2f} €',
                f'{float(item.get("discount", 0)):.2f} %',
                f'{float(item.get("vat", 0)):.2f} %',
                f'{float(item["total"]):.2f} €',
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.lbl_subtotal.setText(f'Osnova: {calculation["subtotal"]:.2f} €')
        self.lbl_discount.setText(f'Popust: {calculation["discount"]:.2f} €')
        self.lbl_vat.setText(f'DDV: {calculation["vat"]:.2f} €')
        self.lbl_total.setText(f'Skupaj: {calculation["total"]:.2f} €')

    def validate_and_accept(self):
        try:
            required_text(self.number.text(), "Številka")
            if self.customer.currentData() is None:
                raise ValueError("Izbrati morate stranko.")
            if self.valid_until.date() < self.issue_date.date():
                raise ValueError("Datum veljavnosti ne sme biti pred datumom izdaje.")
            if not self.items:
                raise ValueError("Ponudba mora vsebovati vsaj eno postavko.")
            calculate_offer(self.items)
        except ValueError as error:
            QMessageBox.warning(self, "Neveljavna ponudba", str(error))
            return
        self.accept()

    def get_data(self):
        return {
            "number": self.number.text(),
            "customer_id": self.customer.currentData(),
            "issue_date": self.issue_date.date().toString("yyyy-MM-dd"),
            "valid_until": self.valid_until.date().toString("yyyy-MM-dd"),
            "status": self.status.currentText(),
            "notes": self.notes.toPlainText().strip(),
            "items": self.items,
        }
