from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QLabel,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.invoice_repository import invoice_repository
from app.database.payment_repository import payment_repository
from app.utils.money import as_float, format_eur, money
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
        self.lbl_invoice_total = QLabel("0.00 €")
        self.lbl_invoice_total.setObjectName("DetailValue")
        self.lbl_remaining = QLabel("0.00 €")
        self.lbl_remaining.setObjectName("DetailValue")
        self.lbl_due = QLabel("—")
        self.lbl_due.setObjectName("DetailValue")
        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("DetailValue")
        self.amount = QDoubleSpinBox()
        self.amount.setDecimals(2)
        self.amount.setMaximum(9999999.99)
        self.amount.setMinimum(0.01)
        self.amount.setObjectName("EnterpriseFilter")
        self.amount.setMinimumHeight(36)
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
        grid.add("Skupaj", self.lbl_invoice_total, "Preostalo", self.lbl_remaining)
        grid.add("Znesek plačila", self.amount, "Rok", self.lbl_due)
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
        payment_repository.ensure_schema()
        for row in invoice_repository.get_all():
            invoice_id = row[0]
            full = invoice_repository.get_by_id(invoice_id)
            due = full[4] if full else None
            badge = invoice_badge(row[5], due)
            if self.invoice_id == invoice_id or badge in (
                "Neplačano",
                "Zapadlo",
                "Osnutek",
                "Delno plačano",
            ):
                label = f"{row[1]}  ·  {row[3]}  ·  {format_eur(row[4])}"
                self.invoice.addItem(label, invoice_id)
        self._show_invoice()

    def _show_invoice(self):
        invoice_id = self.invoice.currentData()
        if invoice_id is None:
            self.lbl_customer.setText("—")
            self.lbl_invoice_total.setText("0.00 €")
            self.lbl_remaining.setText("0.00 €")
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
        total = listing[4] if listing else 0
        remaining = payment_repository.remaining(invoice_id, total)
        self.lbl_customer.setText(str(listing[3] if listing else "—"))
        self.lbl_invoice_total.setText(format_eur(total))
        self.lbl_remaining.setText(format_eur(remaining))
        self.lbl_due.setText(str(due or "—"))
        self.lbl_status.setText(invoice_badge(listing[5] if listing else "", due))
        self.amount.setMaximum(max(as_float(remaining), 0.01))
        self.amount.setValue(as_float(remaining) if remaining > 0 else 0.01)
        raw_status = (full[5] or "").strip() if full else ""
        self.btn_save.setEnabled(remaining > 0 and raw_status != "Storniran")

    def save(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast

        if not allow("write", self):
            return
        invoice_id = self.invoice.currentData()
        if invoice_id is None:
            return

        full = invoice_repository.get_by_id(invoice_id)
        if full is None:
            return
        if (full[5] or "").strip() == "Storniran":
            toast(self, "Storniranega računa ni mogoče plačati.")
            return
        total = float(full[9] or 0)
        remaining = payment_repository.remaining(invoice_id, total)
        amount = money(self.amount.value())
        if amount <= 0:
            toast(self, "Znesek mora biti večji od 0.")
            return
        if amount > money(remaining) + money("0.01"):
            toast(self, "Znesek presega preostalo vsoto.")
            return

        paid = self.paid_date.date().toString("yyyy-MM-dd")
        method = self.method.currentText()
        payment_repository.add(invoice_id, paid, amount, method)
        status = payment_repository.sync_invoice_status(invoice_id, total)

        line = f"[PLAČILO] {paid} · {method} · {format_eur(amount)}"
        notes = (full[10] or "").rstrip()
        notes = f"{notes}\n{line}".strip() if notes else line
        invoice_repository.update_notes(invoice_id, notes)

        audit("edit", f"payment:{invoice_id}:{status}")
        toast(self, f"Plačilo shranjeno ({status}).")
        self.accept()
