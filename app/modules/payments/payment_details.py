from PySide6.QtWidgets import QFormLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from app.core.ui.layouts import vertical_scroll
from app.core.date_format import format_date
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.invoices.status_badge import invoice_badge


class PaymentDetails(QWidget):

    def __init__(self):
        super().__init__()

        self.invoice_id = None
        self.setObjectName("PaymentDetails")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Podrobnosti terjatve")
        title.setObjectName("SectionTitle")
        card.body.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        self.lblNumber = QLabel("-")
        self.lblCustomer = QLabel("-")
        self.lblDate = QLabel("-")
        self.lblDue = QLabel("-")
        self.lblStatus = QLabel("-")
        self.lblTotal = QLabel("0.00 €")
        self.lblReminder = QLabel("Ni poslanih opominov")

        for label in (
            self.lblNumber,
            self.lblCustomer,
            self.lblDate,
            self.lblDue,
            self.lblStatus,
            self.lblTotal,
            self.lblReminder,
        ):
            label.setObjectName("DetailValue")
            label.setWordWrap(True)

        form.addRow("Račun", self.lblNumber)
        form.addRow("Stranka", self.lblCustomer)
        form.addRow("Datum", self.lblDate)
        form.addRow("Rok", self.lblDue)
        form.addRow("Status", self.lblStatus)
        form.addRow("Znesek", self.lblTotal)
        form.addRow("Opomini", self.lblReminder)
        card.body.addLayout(form)

        history_title = QLabel("Zgodovina opominov")
        history_title.setObjectName("SectionTitle")
        self.reminderHistory = QListWidget()
        self.reminderHistory.setMinimumHeight(100)
        self.reminderHistory.setMaximumHeight(160)
        card.body.addWidget(history_title)
        card.body.addWidget(self.reminderHistory)

        self.payButton = QPushButton("Zabeleži plačilo")
        self.payButton.setObjectName("PrimaryButton")
        self.invoiceButton = QPushButton("Odpri račun")
        self.invoiceButton.setObjectName("SecondaryButton")
        self.payButton.setMinimumHeight(36)
        self.invoiceButton.setMinimumHeight(36)
        card.body.addWidget(self.payButton)
        card.body.addWidget(self.invoiceButton)
        card.body.addStretch()
        layout.addWidget(vertical_scroll(card))

    def clear(self):
        self.invoice_id = None
        self.lblNumber.setText("-")
        self.lblCustomer.setText("-")
        self.lblDate.setText("-")
        self.lblDue.setText("-")
        self.lblStatus.setText("-")
        self.lblTotal.setText("0.00 €")
        self.lblReminder.setText("Ni poslanih opominov")
        self.reminderHistory.clear()

    def load_row(self, row):
        self.invoice_id = row[0]
        self.lblNumber.setText(str(row[1]))
        self.lblCustomer.setText(str(row[2]))
        self.lblDate.setText(format_date(row[3], fallback="-"))
        self.lblDue.setText(format_date(row[4], fallback="-"))
        self.lblStatus.setText(invoice_badge(row[6], row[4]))
        try:
            self.lblTotal.setText(f"{float(row[5]):,.2f} €".replace(",", " "))
        except (TypeError, ValueError):
            self.lblTotal.setText("0.00 €")

    def set_reminder_summary(self, summary):
        count = int((summary or {}).get("count", 0))
        if not count:
            self.lblReminder.setText("Ni poslanih opominov")
            return
        level = int(summary.get("last_level", 0))
        sent = format_date(str(summary.get("last_sent", ""))[:10], fallback="-")
        self.lblReminder.setText(f"{count} · zadnji: {level}. stopnja · {sent}")

    def set_reminder_history(self, rows):
        self.reminderHistory.clear()
        if not rows:
            self.reminderHistory.addItem("Ni poslanih opominov")
            return
        for row in rows:
            sent = format_date(str(row[2] or "")[:10], fallback="-")
            try:
                remaining = f"{float(row[5] or 0):,.2f} €".replace(",", " ")
            except (TypeError, ValueError):
                remaining = "0.00 €"
            recipient = row[3] or "—"
            self.reminderHistory.addItem(
                f"{row[1]}. opomin · {sent} · {remaining} · {recipient}"
            )
