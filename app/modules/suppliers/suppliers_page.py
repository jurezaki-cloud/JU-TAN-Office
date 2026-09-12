from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.suppliers.models.supplier_table_model import SupplierTableModel
from app.modules.suppliers.suppliers_controller import SuppliersController
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.suppliers.supplier_dialog import SupplierDialog
from app.widgets.suppliers.supplier_table import SupplierTable
from app.widgets.suppliers.supplier_toolbar import SupplierToolbar


class SuppliersPage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SuppliersPage")
        self.controller = SuppliersController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Dobavitelji")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        self.actions = SupplierToolbar()
        self.search = self.actions.search
        layout.addWidget(self.actions)

        self.table = SupplierTable()
        self.model = SupplierTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(5, StatusBadgeDelegate(self.table))

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        self.empty_state = EmptyStateCard(
            "Ni dobaviteljev",
            "Dodajte prvega dobavitelja za nabavo.",
        )
        self.empty_state.action_clicked.connect(self.new_supplier)
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(table_card)
        layout.addWidget(self.content_stack, 1)

        self.actions.new_clicked.connect(self.new_supplier)
        self.actions.edit_clicked.connect(self.edit_supplier)
        self.actions.delete_clicked.connect(self.delete_supplier)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.filter_changed.connect(self.refresh)
        self.table.doubleClicked.connect(lambda _: self.edit_supplier())
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.suppliers", tables=[self.table], fields=[self.search, self.actions.status])
        self.refresh()

    def refresh(self) -> None:
        rows = self.controller.list_rows(
            self.search.text(),
            self.actions.status.currentData() or "all",
        )
        self.model.refresh(rows)
        self.content_stack.setCurrentIndex(0 if self.model.rowCount() == 0 else 1)

    def new_supplier(self) -> None:
        dialog = SupplierDialog(self)
        if dialog.exec():
            self.controller.save(None, dialog.get_data())
            self.refresh()

    def edit_supplier(self) -> None:
        supplier_id = self._selected_id()
        if supplier_id is None:
            QMessageBox.information(self, "Dobavitelji", "Najprej izberi dobavitelja.")
            return
        dialog = SupplierDialog(self, self.controller.as_dict(supplier_id))
        if dialog.exec():
            self.controller.save(supplier_id, dialog.get_data())
            self.refresh()

    def delete_supplier(self) -> None:
        supplier_id = self._selected_id()
        if supplier_id is None:
            QMessageBox.information(self, "Dobavitelji", "Najprej izberi dobavitelja.")
            return
        if QMessageBox.question(self, "Dobavitelji", "Izbrisati dobavitelja?") != QMessageBox.Yes:
            return
        try:
            self.controller.delete(supplier_id)
        except Exception as exc:
            QMessageBox.warning(self, "Dobavitelji", str(exc))
            return
        self.refresh()

    def _selected_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.supplier_id(indexes[0].row())
