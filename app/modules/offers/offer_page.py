from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSplitter,
    QMessageBox,
)
from app.database.offer_repository import CONVERTED_OFFER_MESSAGE, offer_repository
from app.pdf.pdf_export import pdf_export
from app.services.offer_service import offer_service
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import
from app.modules.offers.models.offer_table_model import OfferTableModel
from app.modules.offers.offer_dialog import OfferDialog
from app.modules.offers.offer_details import OfferDetails
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.common import DocumentListToolbar, PageHeader, ResponsiveStackedWidget
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.offers.offer_actions import OfferActions
from app.widgets.offers.offer_table import OfferTable
from app.widgets.offers.search_field import OfferSearch
from app.widgets.offers.status_badge import offer_badge
from app.widgets.offers.status_bar import OfferStatusBar

class OfferPage(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("OfferPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        title = QLabel("Ponudbe")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)
        self.header = PageHeader(
            "Ponudbe",
            "Priprava, spremljanje in pretvorba ponudb v račune.",
        )
        layout.addWidget(self.header)
        toolbar = DocumentListToolbar()
        self.actions = OfferActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_delete = self.actions.btn_delete
        self.btn_pdf = self.actions.btn_pdf
        self.btn_invoice = self.actions.btn_invoice
        self.btn_refresh = self.actions.btn_refresh
        self.search_field = OfferSearch()
        self.search = self.search_field.input
        toolbar.layout.addWidget(self.search_field, 1)
        toolbar.layout.addWidget(self.actions, 0)
        layout.addWidget(toolbar)
        self.table = OfferTable()
        self.model = OfferTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(4, StatusBadgeDelegate(self.table))
        self.details = OfferDetails()
        self.details.setMinimumWidth(280)
        table_card = EnterpriseCard("DocumentListCard")
        table_card.body.setContentsMargins(0, 0, 0, 0)
        table_card.body.setSpacing(0)
        table_card.body.addWidget(self.table)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("OfferSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)
        self.empty_state = EmptyStateCard(
            "Ni ponudb",
            "Ustvarite prvo ponudbo, da začnete evidenco.",
            action_text="Nova ponudba",
        )
        self.empty_state.action_clicked.connect(self.new_offer)
        self.content_stack = ResponsiveStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)
        layout.addWidget(self.content_stack, 1)
        self.status = OfferStatusBar()
        layout.addWidget(self.status)
        self.btn_new.clicked.connect(self.new_offer)
        self.btn_edit.clicked.connect(self.edit_offer)
        self.btn_delete.clicked.connect(self.delete_offer)
        self.actions.pdf_clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "offers"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "offers", self.refresh)
        )
        self.actions.invoice_clicked.connect(self.convert_invoice)
        self.actions.refresh_clicked.connect(self.refresh)
        from app.core.ui.debounce import Debouncer
        self._search_debounced = Debouncer(self.search_changed, 180, self)
        self.search.textChanged.connect(self._search_debounced)
        self.actions.filter_changed.connect(self._apply_view)
        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(lambda _: self.edit_offer())
        self.details.editButton.clicked.connect(self.edit_offer)
        self.details.deleteButton.clicked.connect(self.delete_offer)
        self.table.selectionModel().selectionChanged.connect(self._update_status)
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.offers", splitters=[splitter], tables=[self.table], fields=[self.search, self.actions.filter])
        self.refresh()

    def refresh(self):
        self._apply_view()

    def search_changed(self, text):
        self._apply_view()

    def new_offer(self):
        dialog = OfferDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_offer(self):
        offer_id = self.selected_offer()
        if offer_id is None:
            QMessageBox.information(
                self,
                "Ponudbe",
                "Najprej izberi ponudbo.",
            )
            return
        if offer_service.is_converted(offer_id):
            QMessageBox.information(
                self,
                "Ponudbe",
                CONVERTED_OFFER_MESSAGE,
            )
            dialog = OfferDialog(self, offer_id=offer_id, read_only=True)
            dialog.exec()
            return
        dialog = OfferDialog(self, offer_id=offer_id)
        if dialog.exec():
            self.refresh()
            self._reload_details(offer_id)

    def delete_offer(self):
        offer_id = self.selected_offer()
        if offer_id is None:
            QMessageBox.information(
                self,
                "Ponudbe",
                "Najprej izberi ponudbo.",
            )
            return
        if offer_service.is_converted(offer_id):
            QMessageBox.warning(self, "Ponudbe", CONVERTED_OFFER_MESSAGE)
            return
        reply = QMessageBox.question(
            self,
            "Ponudbe",
            "Ali res želiš izbrisati ponudbo?",
        )
        if reply == QMessageBox.Yes:
            from app.core.permissions import allow, audit
            if not allow("delete", self):
                return
            try:
                offer_repository.delete_items(offer_id)
                offer_repository.delete(offer_id)
            except ValueError as exc:
                QMessageBox.warning(self, "Ponudbe", str(exc))
                return
            audit("delete", f"offer:{offer_id}")
            self.details.clear()
            self.refresh()

    def export_pdf(self):
        offer_id = self.selected_offer()
        if offer_id is None:
            QMessageBox.information(
                self,
                "Ponudbe",
                "Najprej izberi ponudbo.",
            )
            return
        try:
            path = pdf_export.export_offer(offer_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    def convert_invoice(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast
        if not allow("write", self):
            return
        offer_id = self.selected_offer()
        if offer_id is None:
            QMessageBox.information(self, "Ponudbe", "Izberite ponudbo.")
            return
        offer = offer_repository.get_by_id(offer_id)
        if offer is None:
            QMessageBox.warning(self, "Ponudbe", "Ponudba ne obstaja.")
            return
        if offer_service.is_converted(offer_id):
            QMessageBox.warning(
                self,
                "Ponudbe",
                "Ponudba je že pretvorjena v račun. Ponovna pretvorba ni dovoljena.",
            )
            return
        confirm = QMessageBox.question(
            self,
            "Pretvori v račun",
            f"Pretvorim ponudbo {offer[1]} v nov račun?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            invoice_id, number = offer_service.convert_to_invoice(offer_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Ponudbe", str(exc))
            return
        audit("create", f"invoice_from_offer:{offer_id}->{invoice_id}")
        self.refresh()
        self._reload_details(offer_id)
        toast(self, f"Račun {number} je ustvarjen.")
        QMessageBox.information(
            self,
            "Račun",
            f"Ponudba je pretvorjena v račun {number}.",
        )

    def selected_offer(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.offer_id(indexes[0].row())

    def show_details(self, index):
        offer = self.model.offers[index.row()]
        self.details.load_offer(offer)
        self._update_status()

    def _reload_details(self, offer_id):
        """Reload the details panel from persisted list data for offer_id."""
        for row in self.model.offers:
            if row[0] == offer_id:
                self.details.load_offer(row)
                return
        # Offer may be filtered out of the current view; clear stale panel.
        if self.details.offer_id == offer_id:
            self.details.clear()

    def _apply_view(self, *_args):
        text = self.search.text().strip().lower()
        selected_detail_id = self.details.offer_id
        offers = list(offer_repository.get_all())
        if text:
            offers = [
                row for row in offers
                if text in str(row[1] or "").lower()
                or text in str(row[2] or "").lower()
            ]
        selected = self.actions.filter.currentData()
        if selected and selected != "all":
            offers = [
                row for row in offers
                if offer_badge(row[5], row[4]) == selected
            ]
        self.model.refresh(offers)
        self._sync_empty_state(text, selected)
        if selected_detail_id is not None:
            self._reload_details(selected_detail_id)
        self._update_status()

    def _sync_empty_state(self, text, selected):
        if self.model.rowCount() == 0:
            if text or (selected and selected != "all"):
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskanjem ali statusnim filtrom.",
                )
            else:
                self.empty_state.set_message(
                    "Ni ponudb",
                    "Ustvarite prvo ponudbo, da začnete evidenco.",
                )
            self.content_stack.setCurrentIndex(0)
        else:
            self.content_stack.setCurrentIndex(1)

    def _update_status(self, *_args):
        self.status.set_count(self.model.rowCount())
        offer_id = self.selected_offer()
        if offer_id is None:
            self.status.set_selected(None)
            return
        row = self.table.selectionModel().selectedRows()[0].row()
        self.status.set_selected(str(self.model.offers[row][1]))
