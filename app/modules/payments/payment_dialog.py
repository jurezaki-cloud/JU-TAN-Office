from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QLabel,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.invoice_repository import invoice_repository
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.invoices.status_badge import invoice_badge


class PaymentDialog(EnterpriseDialog):

    def __init__(self, parent=None, invoice_id=None):
        super().__init__(
            parent,
            title="Plačilo",
            heading="Zabeleži plačilo",
            size="SMALL",
            state_key="dialog.payment",
            save_text="Potrdi plačilo",
        )
        self.invoice_id = invoice_id
        self.setObjectName("PaymentDialog")
        self.bind_save(self.save)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.invoice = QComboBox()
        self.lbl_customer = QLabel("—")
        self.lbl_customer.setObjectName("DetailValue")
        self.lbl_amount = QLabel("0.00 €")
        self.lbl_amount.setObjectName("DetailValue")
        self.lbl_due = QLabel("—")
        self.lbl_due.setObjectName("DetailValue")
        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("DetailValue")
        self.paid_date = QDateEdit()
        self.paid_date.setCalendarPopup(True)
        self.paid_date.setDate(QDate.currentDate())
        self.paid_date.setObjectName("EnterpriseFilter")
        self.paid_date.setMinimumHeight(36)
        self.method = QComboBox()
        self.method.setObjectName("EnterpriseFilter")
        self.method.setMinimumHeight(36)
        self.method.addItems(["Nakazilo", "Gotovina", "Kartica", "Kompenzacija"])
        grid.add("Račun", self.invoice, "Stranka", self.lbl_customer)
        grid.add("Znesek", self.lbl_amount, "Rok", self.lbl_due)
        grid.add("Status", self.lbl_status, "Datum plačila", self.paid_date)
        grid.add("Način", self.method)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        self.invoice.currentIndexChanged.connect(self._show_invoice)
        self._load_invoices()
        if self.invoice_id is not None:
            index = self.invoice.findData(self.invoice_id)
            if index >= 0:
                self.invoice.setCurrentIndex(index)
            self.invoice.setEnabled(False)

    def _load_invoices(self):
        self.invoice.clear()
        for row in invoice_repository.get_all():
            invoice_id = row[0]
            full = invoice_repository.get_by_id(invoice_id)
            due = full[4] if full else None
            badge = invoice_badge(row[5], due)
            if self.invoice_id == invoice_id or badge in ("Neplačano", "Zapadlo", "Osnutek"):
                label = f"{row[1]}  ·  {row[3]}  ·  {self._money(row[4])}"
                self.invoice.addItem(label, invoice_id)
        self._show_invoice()

    def _show_invoice(self):
        invoice_id = self.invoice.currentData()
        if invoice_id is None:
            self.lbl_customer.setText("—")
            self.lbl_amount.setText("0.00 €")
            self.lbl_due.setText("—")
            self.lbl_status.setText("—")
            self.btn_save.setEnabled(False)
            return

        listing = next(
            (row for row in invoice_repository.get_all() if row[0] == invoice_id),
            None,
        )
        full = invoice_repository.get_by_id(invoice_id)
        due = full[4] if full else None
        self.lbl_customer.setText(str(listing[3] if listing else "—"))
        self.lbl_amount.setText(self._money(listing[4] if listing else 0))
        self.lbl_due.setText(str(due or "—"))
        self.lbl_status.setText(invoice_badge(listing[5] if listing else "", due))
        self.btn_save.setEnabled(True)

    def save(self):
        invoice_id = self.invoice.currentData()
        if invoice_id is None:
            return

        paid = self.paid_date.date().toString("yyyy-MM-dd")
        method = self.method.currentText()
        line = f"[PLAČILO] {paid} · {method}"
        full = invoice_repository.get_by_id(invoice_id)
        notes = (full[10] or "").rstrip() if full else ""
        if line not in notes:
            notes = f"{notes}\n{line}".strip() if notes else line
            invoice_repository.update_notes(invoice_id, notes)
        invoice_repository.mark_paid(invoice_id)
        self.accept()

    @staticmethod
    def _money(value) -> str:
        try:
            return f"{float(value):,.2f} €".replace(",", " ")
        except (TypeError, ValueError):
            return "0.00 €"
