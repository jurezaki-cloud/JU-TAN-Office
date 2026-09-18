from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import (
    QFileDialog, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableView, QVBoxLayout, QWidget,
)

from app.database.invoice_repository import invoice_repository
from app.database.repository import customer_repository
from app.database.settings_repository import settings_repository
from app.invoices.dialogs import PaymentDialog
from app.services.invoice_pdf import generate_invoice_pdf
from app.widgets.messages import show_error


class InvoiceTableModel(QAbstractTableModel):
    headers = ["Številka", "Stranka", "Izdano", "Zapade", "Status", "Skupaj", "Plačano"]

    def __init__(self):
        super().__init__()
        self.invoices = []

    def refresh(self, invoices):
        self.beginResetModel(); self.invoices = invoices; self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.invoices)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.invoices[index.row()]
        values = [row[1], row[2], row[3], row[4], row[5], f"{row[6]:.2f} €", f"{row[7]:.2f} €"]
        return values[index.column()]

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None


class Invoices(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Računi")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:8px;")
        layout.addWidget(title)
        actions = QHBoxLayout()
        self.btn_payment = QPushButton("💶 Zabeleži plačilo")
        self.btn_pdf = QPushButton("📄 Izvozi PDF")
        self.btn_refresh = QPushButton("🔄 Osveži")
        for button in (self.btn_payment, self.btn_pdf, self.btn_refresh):
            actions.addWidget(button)
        actions.addStretch(); layout.addLayout(actions)
        self.table = QTableView()
        self.model = InvoiceTableModel(); self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.btn_payment.clicked.connect(self.add_payment)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        try: self.model.refresh(invoice_repository.get_all())
        except Exception as error: show_error(self, error, "Računov ni mogoče naložiti")

    def current_id(self):
        index = self.table.currentIndex()
        return self.model.invoices[index.row()][0] if index.isValid() else None

    def add_payment(self):
        invoice_id = self.current_id()
        if invoice_id is None:
            QMessageBox.information(self, "Plačilo", "Najprej izberite račun."); return
        try:
            invoice = invoice_repository.get_by_id(invoice_id)
            remaining = invoice[10] - invoice[11]
            if remaining <= 0:
                QMessageBox.information(self, "Plačilo", "Račun je že v celoti plačan."); return
            dialog = PaymentDialog(remaining, self)
            if not dialog.exec(): return
            data = dialog.get_data()
            invoice_repository.add_payment(invoice_id, **data)
            self.refresh()
        except Exception as error: show_error(self, error, "Plačila ni mogoče shraniti")

    def export_pdf(self):
        invoice_id = self.current_id()
        if invoice_id is None:
            QMessageBox.information(self, "PDF", "Najprej izberite račun."); return
        try:
            invoice = invoice_repository.get_by_id(invoice_id)
            customer = customer_repository.get_by_id(invoice[2])
            items = invoice_repository.get_items(invoice_id)
            payments = invoice_repository.get_payments(invoice_id)
            path, _ = QFileDialog.getSaveFileName(
                self, "Shrani račun PDF", f"Racun-{invoice[1]}.pdf", "PDF dokumenti (*.pdf)"
            )
            if not path: return
            if not path.lower().endswith(".pdf"): path += ".pdf"
            generate_invoice_pdf(
                path, invoice, customer, items, payments,
                settings_repository.get(),
            )
            QMessageBox.information(self, "PDF", "Račun je uspešno izvožen.")
        except Exception as error: show_error(self, error, "PDF-ja ni mogoče ustvariti")


class PaymentTableModel(QAbstractTableModel):
    headers = ["Datum", "Račun", "Stranka", "Znesek", "Način", "Referenca"]

    def __init__(self):
        super().__init__(); self.payments = []

    def refresh(self, payments):
        self.beginResetModel(); self.payments = payments; self.endResetModel()

    def rowCount(self, parent=None): return len(self.payments)
    def columnCount(self, parent=None): return len(self.headers)

    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole: return None
        row = self.payments[index.row()]
        values = [row[1], row[2], row[3], f"{row[4]:.2f} €", row[5] or "", row[6] or ""]
        return values[index.column()]

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole: return self.headers[section]
        return None


class Payments(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Plačila")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:8px;")
        layout.addWidget(title)
        self.btn_refresh = QPushButton("🔄 Osveži")
        layout.addWidget(self.btn_refresh, alignment=Qt.AlignLeft)
        self.table = QTableView(); self.model = PaymentTableModel()
        self.table.setModel(self.model); self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.btn_refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self):
        try: self.model.refresh(invoice_repository.get_all_payments())
        except Exception as error: show_error(self, error, "Plačil ni mogoče naložiti")
