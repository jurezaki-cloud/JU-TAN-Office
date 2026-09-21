from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QMessageBox,
)
from app.core.ui.notify import toast, toast_info
from app.database.invoice_repository import invoice_repository
from app.pdf.pdf_export import pdf_export
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import
from app.modules.invoices.models.invoice_table_model import InvoiceTableModel
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.common import DocumentListToolbar, PageHeader, ResponsiveStackedWidget
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.invoice_actions import InvoiceActions
from app.widgets.invoices.invoice_table import InvoiceTable
from app.widgets.invoices.search_field import InvoiceSearch
from app.widgets.invoices.status_badge import StatusBadgeDelegate, invoice_badge
from app.widgets.invoices.status_bar import InvoiceStatusBar

class InvoicePage(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("InvoicePage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        title = QLabel("Računi")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)
        self.header = PageHeader(
            "Računi",
            "Pregled, iskanje in upravljanje izdanih računov.",
        )
        layout.addWidget(self.header)
        toolbar = DocumentListToolbar()
        self.search_field = InvoiceSearch()
        self.search = self.search_field.input
        self.search.setMinimumWidth(260)
        self.actions = InvoiceActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_duplicate = self.actions.btn_duplicate
        self.btn_delete = self.actions.btn_delete
        self.btn_pdf = self.actions.btn_pdf
        self.btn_refresh = self.actions.btn_refresh
        # Pattern: [ Search ] [Status] [actions…]
        toolbar.layout.addWidget(self.search_field, 1)
        # Re-parent filter + actions without duplicating the search.
        toolbar.layout.addWidget(self.actions, 0)
        layout.addWidget(toolbar)
        self.table = InvoiceTable()
        self.model = InvoiceTableModel()
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)
        self.table.setItemDelegateForColumn(5, StatusBadgeDelegate(self.table))
        table_card = EnterpriseCard("DocumentListCard")
        table_card.body.setContentsMargins(0, 0, 0, 0)
        table_card.body.setSpacing(0)
        table_card.body.addWidget(self.table)
        self.empty_state = EmptyStateCard(
            "Ni računov",
            "Ustvarite prvi račun ali spremenite iskalni filter.",
            action_text="Nov račun",
        )
        self.content_stack = ResponsiveStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(table_card)
        layout.addWidget(self.content_stack, 1)
        self.status = InvoiceStatusBar()
        layout.addWidget(self.status)
        self.empty_state.action_clicked.connect(self.new_invoice)
        self.btn_new.clicked.connect(self.new_invoice)
        self.btn_edit.clicked.connect(self.edit_invoice)
        self.btn_delete.clicked.connect(self.delete_invoice)
        # InvoiceActions owns overflow actions via semantic signals.
        self.actions.duplicate_clicked.connect(self.duplicate_invoice)
        self.actions.pdf_clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "invoices"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "invoices", self.refresh)
        )
        self.actions.refresh_clicked.connect(self.refresh)
        from app.core.pagination import IncrementalLoader
        from app.core.ui.debounce import Debouncer
        self._loader = IncrementalLoader(
            lambda offset, size: invoice_repository.list_page(
                self.search.text().strip(), limit=size, offset=offset
            )
        )
        self._search_debounced = Debouncer(self.search_changed, 180, self)
        self.search.textChanged.connect(self._search_debounced)
        self.actions.filter_changed.connect(self._apply_view)
        self.table.doubleClicked.connect(lambda _: self.edit_invoice())
        self.table.selectionModel().selectionChanged.connect(
            self._update_status
        )
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.invoices", tables=[self.table], fields=[self.search, self.actions.filter])
        self.table.verticalScrollBar().valueChanged.connect(self._maybe_more)
        self.refresh()

    def new_invoice(self):
        dialog = InvoiceDialog(self)
        if dialog.exec():
            self.refresh()
            toast(self, "Račun shranjen")

    def edit_invoice(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            toast_info(
                self,
                "Najprej izberi račun."
            )
            return
        dialog = InvoiceDialog(
            self,
            invoice_id=invoice_id
        )
        if dialog.exec():
            self.refresh()
            toast(self, "Račun shranjen")

    def duplicate_invoice(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            toast_info(
                self,
                "Najprej izberi račun."
            )
            return
        new_id = invoice_repository.duplicate(invoice_id)
        if new_id is None:
            QMessageBox.warning(
                self,
                "Računi",
                "Računa ni bilo mogoče kopirati."
            )
            return
        self.refresh()
        dialog = InvoiceDialog(
            self,
            invoice_id=new_id
        )
        if dialog.exec():
            self.refresh()
            toast(self, "Račun shranjen")

    def export_pdf(self):
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            toast_info(
                self,
                "Najprej izberi račun.",
            )
            return
        try:
            toast_info(self, "Ustvarjam PDF ...")
            # PDF generation is intentionally synchronous here. ReportLab, permissions,
            # SQLite repositories and desktop opening all participate in this workflow;
            # keeping it on the GUI thread makes failures visible and avoids silent
            # worker-callback failures in the packaged Windows application.
            path = pdf_export.export_invoice(invoice_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", f"PDF ni bilo mogoče ustvariti:\n{exc}")

    def refresh(self):
        self._apply_view()

    def search_changed(self, text):
        self._apply_view()

    def selected_invoice(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.invoice_id(indexes[0].row())

    def delete_invoice(self):
        from app.core.permissions import allow, audit
        if not allow("delete", self):
            return
        invoice_id = self.selected_invoice()
        if invoice_id is None:
            toast_info(
                self,
                "Najprej izberi račun."
            )
            return
        reply = QMessageBox.question(
            self,
            "Storniranje računa",
            "Račun bo označen kot storniran in bo ostal v evidenci. Nadaljujem?"
        )
        if reply == QMessageBox.Yes:
            invoice_repository.cancel(invoice_id)
            audit("edit", f"invoice:{invoice_id}:cancelled")
            self.refresh()

    def _apply_view(self, *_args):
        text = self.search.text().strip()
        invoices = self._loader.first()
        decorated = self._decorate(invoices)
        selected = self.actions.filter.currentData()
        if selected and selected != "all":
            decorated = [
                row for row in decorated
                if invoice_badge(row[5], row[6] if len(row) > 6 else None) == selected
            ]
        self.model.refresh(decorated)
        self._sync_empty_state(text, selected)
        self._update_status()

    def _maybe_more(self, value: int) -> None:
        bar = self.table.verticalScrollBar()
        if self._loader.exhausted or value < bar.maximum() - 12:
            return
        more = self._decorate(self._loader.more())
        selected = self.actions.filter.currentData()
        if selected and selected != "all":
            more = [
                row for row in more
                if invoice_badge(row[5], row[6] if len(row) > 6 else None) == selected
            ]
        self.model.append_rows(more)
        self._update_status()

    def _decorate(self, invoices):
        rows = []
        for invoice in invoices:
            if len(invoice) > 6:
                rows.append(tuple(invoice))
            else:
                full = invoice_repository.get_by_id(invoice[0])
                due = full[4] if full else None
                rows.append(tuple(invoice) + (due,))
        return rows

    def _sync_empty_state(self, text, selected):
        if self.model.rowCount() == 0:
            if text or (selected and selected != "all"):
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskanjem ali statusnim filtrom.",
                )
            else:
                self.empty_state.set_message(
                    "Ni računov",
                    "Ustvarite prvi račun, da začnete evidenco.",
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
        number = self.model.invoices[row][1]
        self.status.set_selected(str(number))
