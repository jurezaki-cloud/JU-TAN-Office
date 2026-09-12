from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.invoice_repository import invoice_repository
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.modules.payments.models.payment_table_model import PaymentTableModel
from app.modules.payments.payment_details import PaymentDetails
from app.modules.payments.payment_dialog import PaymentDialog
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate, invoice_badge
from app.widgets.payments.payment_actions import PaymentActions
from app.widgets.payments.payment_table import PaymentTable
from app.widgets.payments.search_field import PaymentSearch
from app.widgets.payments.status_bar import PaymentStatusBar


class PaymentPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("PaymentPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Plačila")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(16)
        self.kpi_received = KpiCard("Prejeto", "0,00 €", "Plačani računi")
        self.kpi_open = KpiCard("Odprto", "0,00 €", "Neplačano")
        self.kpi_overdue = KpiCard("Zapadlo", "0,00 €", "Po roku plačila")
        self.kpi_count = KpiCard("Plačani računi", "0", "Število likvidacij")
        for card in (
            self.kpi_received,
            self.kpi_open,
            self.kpi_overdue,
            self.kpi_count,
        ):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        top = QHBoxLayout()
        top.setSpacing(12)

        self.actions = PaymentActions()
        self.btn_new = self.actions.btn_new
        self.btn_unpaid = self.actions.btn_unpaid
        self.btn_invoice = self.actions.btn_invoice
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = PaymentSearch()
        self.search = self.search_field.input

        top.addWidget(self.actions)
        top.addStretch()
        top.addWidget(self.search_field)
        layout.addLayout(top)

        self.table = PaymentTable()
        self.model = PaymentTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(5, StatusBadgeDelegate(self.table))

        self.details = PaymentDetails()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        splitter = QSplitter()
        splitter.setObjectName("PaymentSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.details)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)

        self.empty_state = EmptyStateCard(
            "Ni terjatev",
            "Izdani računi se tukaj pokažejo kot odprta in prejeta plačila.",
        )
        self.empty_state.action_clicked.connect(self.new_payment)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)
        layout.addWidget(self.content_stack, 1)

        self.status = PaymentStatusBar()
        layout.addWidget(self.status)

        self.btn_new.clicked.connect(self.new_payment)
        self.btn_unpaid.clicked.connect(self.mark_unpaid)
        self.btn_invoice.clicked.connect(self.open_invoice)
        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.search_changed)
        self.actions.filter_changed.connect(self._apply_view)
        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(lambda _: self.new_payment())
        self.details.payButton.clicked.connect(self.new_payment)
        self.details.invoiceButton.clicked.connect(self.open_invoice)
        self.table.selectionModel().selectionChanged.connect(self._update_status)

        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.payments", splitters=[splitter], tables=[self.table], fields=[self.search, self.actions.filter])
        self.refresh()

    def refresh(self):
        self._apply_view()

    def search_changed(self, text):
        self._apply_view()

    def new_payment(self):
        invoice_id = self.selected_invoice()
        dialog = PaymentDialog(self, invoice_id=invoice_id)
        if dialog.invoice.count() == 0:
            QMessageBox.information(
                self,
                "Plačila",
                "Ni odprtih računov za likvidacijo.",
            )
            return
        if dialog.exec():
            self.refresh()
            if invoice_id:
                self._reload_details(invoice_id)

    def mark_unpaid(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            QMessageBox.information(
                self,
                "Plačila",
                "Najprej izberi račun.",
            )
            return
        invoice_repository.mark_sent(invoice_id)
        self.refresh()
        self._reload_details(invoice_id)

    def open_invoice(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            QMessageBox.information(
                self,
                "Plačila",
                "Najprej izberi račun.",
            )
            return
        dialog = InvoiceDialog(self, invoice_id=invoice_id)
        if dialog.exec():
            self.refresh()
            self._reload_details(invoice_id)

    def selected_invoice(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.invoice_id(indexes[0].row())

    def show_details(self, index):
        self.details.load_row(self.model.rows[index.row()])
        self._update_status()

    def _reload_details(self, invoice_id):
        for row in self.model.rows:
            if row[0] == invoice_id:
                self.details.load_row(row)
                return
        self.details.clear()

    def _ledger(self):
        text = self.search.text().strip()
        invoices = (
            invoice_repository.search(text)
            if text
            else invoice_repository.get_all()
        )
        rows = []
        for invoice in invoices:
            full = invoice_repository.get_by_id(invoice[0])
            due = full[4] if full else None
            rows.append((
                invoice[0],
                invoice[1],
                invoice[3],
                invoice[2],
                due,
                invoice[4],
                invoice[5],
            ))
        return rows

    def _apply_view(self, *_args):
        rows = self._ledger()
        self._update_kpis(invoice_repository.get_all())

        selected = self.actions.filter.currentData()
        if selected and selected != "all":
            rows = [
                row for row in rows
                if invoice_badge(row[6], row[4]) == selected
            ]

        self.model.refresh(rows)
        self._sync_empty_state(self.search.text().strip(), selected)
        self._update_status()

    def _update_kpis(self, invoices):
        received = 0.0
        open_total = 0.0
        overdue_total = 0.0
        paid_count = 0
        for invoice in invoices:
            full = invoice_repository.get_by_id(invoice[0])
            due = full[4] if full else None
            badge = invoice_badge(invoice[5], due)
            try:
                total = float(invoice[4] or 0)
            except (TypeError, ValueError):
                total = 0.0
            if badge == "Plačano":
                received += total
                paid_count += 1
            elif badge == "Zapadlo":
                overdue_total += total
                open_total += total
            elif badge == "Neplačano":
                open_total += total
        self.kpi_received.set_value(self._money(received))
        self.kpi_open.set_value(self._money(open_total))
        self.kpi_overdue.set_value(self._money(overdue_total))
        self.kpi_count.set_value(str(paid_count))

    def _sync_empty_state(self, text, selected):
        if self.model.rowCount() == 0:
            if text or (selected and selected != "all"):
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskanjem ali statusnim filtrom.",
                )
            else:
                self.empty_state.set_message(
                    "Ni terjatev",
                    "Izdani računi se tukaj pokažejo kot odprta in prejeta plačila.",
                )
            self.content_stack.setCurrentIndex(0)
        else:
            self.content_stack.setCurrentIndex(1)

    def _update_status(self, *_args):
        self.status.set_count(self.model.rowCount())
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            self.status.set_selected(None)
            return
        row = self.table.selectionModel().selectedRows()[0].row()
        self.status.set_selected(str(self.model.rows[row][1]))

    @staticmethod
    def _money(value) -> str:
        try:
            return f"{float(value):,.2f} €".replace(",", " ")
        except (TypeError, ValueError):
            return "0.00 €"
