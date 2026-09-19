from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.notify import toast
from app.modules.purchase.models.purchase_table_model import PurchaseTableModel
from app.modules.purchase.purchase_controller import PurchaseController
from app.pdf.pdf_export import pdf_export
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.purchase.purchase_dialog import PurchaseDialog
from app.widgets.purchase.purchase_table import PurchaseTable
from app.widgets.purchase.purchase_toolbar import PurchaseToolbar
from app.widgets.purchase.receive_dialog import ReceiveDialog


class PurchasePage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PurchasePage")
        self.controller = PurchaseController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Nabava")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(16)
        self.kpi_suppliers = KpiCard("Skupaj dobaviteljev", "0", "Register")
        self.kpi_open = KpiCard("Odprta naročila", "0", "Draft / Ordered / Partial")
        self.kpi_today = KpiCard("Dobave danes", "0", "Prevzemi")
        self.kpi_value = KpiCard("Skupna vrednost naročil", "0,00 €", "Brez preklicanih")
        for card in (self.kpi_suppliers, self.kpi_open, self.kpi_today, self.kpi_value):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        self.actions = PurchaseToolbar()
        self.search = self.actions.search
        layout.addWidget(self.actions)

        self.table = PurchaseTable()
        self.model = PurchaseTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(4, StatusBadgeDelegate(self.table))

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        self.empty_state = EmptyStateCard(
            "Ni nabavnih naročil",
            "Ustvarite prvo nabavo pri dobavitelju.",
        )
        self.empty_state.action_clicked.connect(self.new_purchase)
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(table_card)
        layout.addWidget(self.content_stack, 1)

        self.actions.new_clicked.connect(self.new_purchase)
        self.actions.receive_clicked.connect(self.receive)
        self.actions.print_clicked.connect(self.print_pdf)
        self.actions.pdf_clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(self.export_excel)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.filter_changed.connect(self.refresh)
        self.table.doubleClicked.connect(lambda _: self.edit_purchase())
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.purchase", tables=[self.table], fields=[self.search])
        self.refresh()

    def refresh(self) -> None:
        self.actions.fill_statuses(self.controller.statuses())
        self.actions.fill_suppliers(self.controller.suppliers())
        rows = self.controller.list_rows(
            query=self.search.text(),
            supplier_id=self.actions.supplier.currentData() or "all",
            status=self.actions.status.currentData() or "all",
            date_filter=self.actions.date_mode.currentData() or "all",
            selected_date=self.actions.date.date().toString("yyyy-MM-dd"),
        )
        self.model.refresh(rows)
        self.content_stack.setCurrentIndex(0 if self.model.rowCount() == 0 else 1)
        kpis = self.controller.kpis()
        self.kpi_suppliers.set_value(str(kpis["suppliers"]))
        self.kpi_open.set_value(str(kpis["open_orders"]))
        self.kpi_today.set_value(str(kpis["received_today"]))
        self.kpi_value.set_value(f"{float(kpis['value']):,.2f} €".replace(",", " "))

    def new_purchase(self) -> None:
        if not self.controller.suppliers():
            QMessageBox.information(
                self,
                "Nabava",
                "Najprej dodajte dobavitelja.",
            )
            return
        dialog = PurchaseDialog(self, self.controller)
        if dialog.exec():
            self.refresh()

    def edit_purchase(self) -> None:
        purchase_id = self._selected_id()
        if purchase_id is None:
            QMessageBox.information(self, "Nabava", "Najprej izberi naročilo.")
            return
        dialog = PurchaseDialog(self, self.controller, purchase_id)
        if dialog.exec():
            self.refresh()

    def receive(self) -> None:
        purchase_id = self._selected_id()
        if purchase_id is None:
            QMessageBox.information(self, "Nabava", "Najprej izberi naročilo.")
            return
        if not self.controller.can_receive(purchase_id):
            QMessageBox.information(
                self,
                "Prevzem",
                "Prevzem je mogoč samo za Draft, Ordered ali Partially Received.",
            )
            return
        dialog = ReceiveDialog(self, self.controller, purchase_id)
        if dialog.exec():
            self.refresh()

    def export_pdf(self) -> None:
        purchase_id = self._selected_id()
        if purchase_id is None:
            QMessageBox.information(self, "Nabava", "Najprej izberi naročilo.")
            return
        try:
            path = self.controller.export_pdf(purchase_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    def print_pdf(self) -> None:
        purchase_id = self._selected_id()
        if purchase_id is None:
            QMessageBox.information(self, "Nabava", "Najprej izberi naročilo.")
            return
        try:
            path = self.controller.export_pdf(purchase_id)
            pdf_export.print_pdf(path)
        except Exception as exc:
            QMessageBox.warning(self, "Print", str(exc))

    def export_excel(self) -> None:
        start = str(self.controller.export_start_path())
        path, _ = QFileDialog.getSaveFileName(self, "Excel izvoz", start, "Excel (*.xlsx)")
        if not path:
            return
        self.controller.export_excel(Path(path), self.model.rows)
        toast(self, "Excel izvožen")

    def _selected_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.purchase_id(indexes[0].row())
