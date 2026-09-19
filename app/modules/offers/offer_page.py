from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QMessageBox,
    QStackedWidget,
)

from app.database.offer_repository import offer_repository
from app.pdf.pdf_export import pdf_export
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import
from app.modules.offers.models.offer_table_model import OfferTableModel
from app.modules.offers.offer_dialog import OfferDialog
from app.modules.offers.offer_details import OfferDetails
from app.widgets.cards.enterprise_card import EnterpriseCard
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
        layout.setSpacing(16)

        title = QLabel("Ponudbe")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        top = QHBoxLayout()
        top.setSpacing(12)

        self.actions = OfferActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_delete = self.actions.btn_delete
        self.btn_pdf = self.actions.btn_pdf
        self.btn_invoice = self.actions.btn_invoice
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = OfferSearch()
        self.search = self.search_field.input

        top.addWidget(self.actions)
        top.addStretch()
        top.addWidget(self.search_field)
        layout.addLayout(top)

        self.table = OfferTable()
        self.model = OfferTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(4, StatusBadgeDelegate(self.table))

        self.details = OfferDetails()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        splitter = QSplitter()
        splitter.setObjectName("OfferSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.details)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)

        self.empty_state = EmptyStateCard(
            "Ni ponudb",
            "Ustvarite prvo ponudbo, da začnete evidenco.",
        )
        self.empty_state.action_clicked.connect(self.new_offer)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)
        layout.addWidget(self.content_stack, 1)

        self.status = OfferStatusBar()
        layout.addWidget(self.status)

        self.btn_new.clicked.connect(self.new_offer)
        self.btn_edit.clicked.connect(self.edit_offer)
        self.btn_delete.clicked.connect(self.delete_offer)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "offers"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "offers", self.refresh)
        )
        self.btn_invoice.clicked.connect(self.convert_invoice)
        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.search_changed)
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

        reply = QMessageBox.question(
            self,
            "Ponudbe",
            "Ali res želiš izbrisati ponudbo?",
        )
        if reply == QMessageBox.Yes:
            from app.core.permissions import allow, audit

            if not allow("delete", self):
                return
            offer_repository.delete_items(offer_id)
            offer_repository.delete(offer_id)
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
        from app.database.invoice_repository import invoice_repository
        from datetime import date, timedelta

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

        items = offer_repository.get_items(offer_id)
        if not items:
            QMessageBox.warning(self, "Ponudbe", "Ponudba nima postavk.")
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

        today = date.today()
        due = today + timedelta(days=30)
        number = invoice_repository.get_next_number()
        invoice_id = invoice_repository.add(
            invoice_number=number,
            customer_id=offer[2],
            issue_date=today.isoformat(),
            due_date=due.isoformat(),
            subtotal=float(offer[6] or 0),
            discount=float(offer[7] or 0),
            vat=float(offer[8] or 0),
            total=float(offer[9] or 0),
            notes=(offer[10] or "") + (f"\n[Iz ponudbe {offer[1]}]" if offer[1] else ""),
            status="Izdan",
        )
        invoice_repository.increase_counter()

        for item in items:
            # offer item: id, article_id, code, name, description,
            # quantity, unit, price, discount, vat, total
            invoice_repository.add_item(
                invoice_id=invoice_id,
                article_id=item[1],
                code=item[2],
                name=item[3],
                description=item[4] or "",
                quantity=item[5],
                unit=item[6],
                price=item[7],
                discount=item[8] or 0,
                vat=item[9],
                total=item[10],
            )

        offer_repository.update(
            offer_id,
            customer_id=offer[2],
            issue_date=offer[3],
            valid_until=offer[4],
            status="Sprejeta",
            subtotal=offer[6],
            discount=offer[7],
            vat=offer[8],
            total=offer[9],
            notes=offer[10] or "",
        )
        audit("create", f"invoice_from_offer:{offer_id}->{invoice_id}")
        self.refresh()
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
        for row in self.model.offers:
            if row[0] == offer_id:
                self.details.load_offer(row)
                return

    def _apply_view(self, *_args):
        text = self.search.text().strip().lower()
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
