from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QInputDialog,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.invoice_repository import invoice_repository
from app.database.customer_repository import customer_repository
from app.pdf.pdf_export import pdf_export
from app.widgets.mail_center_dialog import MailCenterDialog
from app.database.payment_repository import payment_repository
from app.database.reminder_repository import reminder_repository
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
from app.services.print_center import print_center


class PaymentPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("PaymentPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Plačila")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(12)
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

        self.actions = PaymentActions()
        self.btn_new = self.actions.btn_new
        self.btn_unpaid = self.actions.btn_unpaid
        self.btn_invoice = self.actions.btn_invoice
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = PaymentSearch()
        self.search = self.search_field.input

        from app.widgets.common.page_chrome import PageToolbar

        toolbar = PageToolbar()
        toolbar.layout.addWidget(self.search_field, 1)
        toolbar.layout.addWidget(self.actions, 0)
        layout.addWidget(toolbar)

        self.table = PaymentTable()
        # Below the KPI row a short window (150 % at the default size) leaves the splitter about
        # 220 px: keep the header and three 44 px rows, and scroll the rest inside the card.
        self.table.setMinimumHeight(176)
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
        self.actions.print_clicked.connect(self.print_payments)
        self.actions.reminder_clicked.connect(self.send_reminder)
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
        from app.core.ui_freeze_diag import span as _diag_span

        with _diag_span("PaymentPage.refresh"):
            self._apply_view()

    def search_changed(self, text):
        self._apply_view()

    def new_payment(self):
        from app.core.ui_freeze_diag import span as _diag_span

        invoice_id = self.selected_invoice()
        with _diag_span("PaymentPage.new_payment", invoice_id=invoice_id):
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

    def send_reminder(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            QMessageBox.information(self, "Payment Center", "Najprej izberi račun.")
            return
        invoice = invoice_repository.get_by_id(invoice_id)
        if invoice is None:
            QMessageBox.warning(self, "Payment Center", "Račun ne obstaja.")
            return
        badge = invoice_badge(invoice[5], invoice[4])
        if badge == "Plačano":
            QMessageBox.information(self, "Payment Center", "Račun je že plačan.")
            return
        if badge == "Stornirano":
            QMessageBox.information(self, "Payment Center", "Za storniran račun opomina ni mogoče poslati.")
            return
        customer = customer_repository.get_by_id(invoice[2]) if invoice[2] else None
        recipient = str(customer[8] or "") if customer else ""
        number = str(invoice[1] or "")
        suggested = reminder_repository.suggested_level(invoice_id, invoice[4])
        labels = ["1. opomin", "2. opomin", "3. opomin"]
        allowed_labels = [labels[suggested - 1]]
        selected, ok = QInputDialog.getItem(
            self, "Payment Center", "Stopnja opomina", allowed_labels, 0, False
        )
        if not ok:
            return
        level = labels.index(selected) + 1
        remaining = payment_repository.remaining(invoice_id, invoice[9] or 0)
        if remaining <= 0:
            QMessageBox.information(self, "Payment Center", "Račun nima odprtega zneska za opomin.")
            return
        try:
            path = pdf_export.export_invoice(invoice_id)
            subject = f"{level}. opomin za plačilo — račun {number}"
            urgency = {
                1: "Prosimo, da odprti znesek poravnate v najkrajšem možnem času.",
                2: "Račun kljub prvemu opominu ostaja odprt. Prosimo za čimprejšnje plačilo.",
                3: "Gre za tretji opomin. Prosimo za takojšnjo ureditev odprte obveznosti.",
            }[level]
            body = (
                f"Spoštovani,\n\nobveščamo vas, da račun {number} še ni v celoti poravnan. "
                f"Odprti znesek znaša {self._money(remaining)}.\n\n{urgency}\n\n"
                f"Če ste račun medtem že poravnali, prosimo prezrite to sporočilo.\n\n"
                f"Lep pozdrav,\nJU-TAN Studio"
            )
            dialog = MailCenterDialog(
                self, recipient=recipient, subject=subject, body=body, attachment=path
            )
            if dialog.exec():
                reminder_repository.add(
                    invoice_id, level, dialog.to.text().strip(),
                    dialog.subject.text().strip(), remaining
                )
                self._reload_details(invoice_id)
        except Exception as exc:
            QMessageBox.warning(self, "Payment Center", str(exc))

    def open_invoice(self):
        from app.core.ui_freeze_diag import span as _diag_span

        invoice_id = self.selected_invoice()
        if invoice_id is None:
            QMessageBox.information(
                self,
                "Plačila",
                "Najprej izberi račun.",
            )
            return
        with _diag_span("PaymentPage.open_invoice", invoice_id=invoice_id):
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
        row = self.model.rows[index.row()]
        self.details.load_row(row)
        self.details.set_reminder_summary(reminder_repository.summary(row[0]))
        self.details.set_reminder_history(reminder_repository.list_for_invoice(row[0]))
        self._update_status()

    def _reload_details(self, invoice_id):
        for row in self.model.rows:
            if row[0] == invoice_id:
                self.details.load_row(row)
                self.details.set_reminder_summary(reminder_repository.summary(invoice_id))
                self.details.set_reminder_history(reminder_repository.list_for_invoice(invoice_id))
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
        from app.core.ui_freeze_diag import span as _diag_span

        with _diag_span("PaymentPage._apply_view"):
            with _diag_span("PaymentPage._ledger"):
                rows = self._ledger()
            with _diag_span("PaymentPage._update_kpis"):
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

    def print_payments(self):
        rows = [
            (row[1], row[2], row[3], row[4], row[5], row[6])
            for row in self.model.rows
        ]
        html = print_center.table_html(
            "Plačila / terjatve",
            ["Račun", "Stranka", "Datum", "Rok", "Znesek", "Status"],
            rows,
        )
        try:
            print_center.print_html(self, html, "Plačila / terjatve")
        except Exception as exc:
            QMessageBox.warning(self, "Print Center", str(exc))

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
            paid = payment_repository.sum_for_invoice(invoice[0])
            remaining = payment_repository.remaining(invoice[0], total)
            if badge != "Stornirano":
                received += paid
            if badge == "Plačano":
                paid_count += 1
            elif badge == "Zapadlo":
                overdue_total += remaining
                open_total += remaining
            elif badge in ("Neplačano", "Delno plačano"):
                open_total += remaining
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
