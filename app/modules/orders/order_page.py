from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QMessageBox,
    QStackedWidget,
)

from app.database.order_repository import order_repository
from app.pdf.pdf_export import pdf_export
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import
from app.modules.orders.models.order_table_model import OrderTableModel
from app.modules.orders.order_dialog import OrderDialog
from app.modules.orders.order_details import OrderDetails
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.orders.order_actions import OrderActions
from app.widgets.orders.order_table import OrderTable
from app.widgets.orders.search_field import OrderSearch
from app.widgets.orders.status_badge import order_badge
from app.widgets.orders.status_bar import OrderStatusBar


class OrderPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("OrderPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Naročila")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        top = QHBoxLayout()
        top.setSpacing(12)

        self.actions = OrderActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_delete = self.actions.btn_delete
        self.btn_pdf = self.actions.btn_pdf
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = OrderSearch()
        self.search = self.search_field.input

        top.addWidget(self.actions)
        top.addStretch()
        top.addWidget(self.search_field)
        layout.addLayout(top)

        self.table = OrderTable()
        self.model = OrderTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(4, StatusBadgeDelegate(self.table))

        self.details = OrderDetails()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        splitter = QSplitter()
        splitter.setObjectName("OrderSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.details)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)

        self.empty_state = EmptyStateCard(
            "Ni naročil",
            "Ustvarite prvo naročilo, da začnete evidenco.",
        )
        self.empty_state.action_clicked.connect(self.new_order)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)
        layout.addWidget(self.content_stack, 1)

        self.status = OrderStatusBar()
        layout.addWidget(self.status)

        self.btn_new.clicked.connect(self.new_order)
        self.btn_edit.clicked.connect(self.edit_order)
        self.btn_delete.clicked.connect(self.delete_order)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "orders"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "orders", self.refresh)
        )
        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.search_changed)
        self.actions.filter_changed.connect(self._apply_view)
        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(lambda _: self.edit_order())
        self.details.editButton.clicked.connect(self.edit_order)
        self.details.deleteButton.clicked.connect(self.delete_order)
        self.table.selectionModel().selectionChanged.connect(self._update_status)

        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.orders", splitters=[splitter], tables=[self.table], fields=[self.search, self.actions.filter])
        self.refresh()

    def refresh(self):
        self._apply_view()

    def search_changed(self, text):
        self._apply_view()

    def new_order(self):
        dialog = OrderDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_order(self):
        order_id = self.selected_order()
        if order_id is None:
            QMessageBox.information(
                self,
                "Naročila",
                "Najprej izberi naročilo.",
            )
            return
        dialog = OrderDialog(self, order_id=order_id)
        if dialog.exec():
            self.refresh()
            self._reload_details(order_id)

    def delete_order(self):
        order_id = self.selected_order()
        if order_id is None:
            QMessageBox.information(
                self,
                "Naročila",
                "Najprej izberi naročilo.",
            )
            return
        reply = QMessageBox.question(
            self,
            "Naročila",
            "Ali res želiš izbrisati naročilo?",
        )
        if reply == QMessageBox.Yes:
            from app.core.permissions import allow, audit

            if not allow("delete", self):
                return
            order_repository.delete(order_id)
            audit("delete", f"order:{order_id}")
            self.details.clear()
            self.refresh()

    def export_pdf(self):
        order_id = self.selected_order()
        if order_id is None:
            QMessageBox.information(
                self,
                "Naročila",
                "Najprej izberi naročilo.",
            )
            return
        try:
            path = pdf_export.export_order(order_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    def selected_order(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.order_id(indexes[0].row())

    def show_details(self, index):
        self.details.load_order(self.model.orders[index.row()])
        self._update_status()

    def _reload_details(self, order_id):
        for row in self.model.orders:
            if row[0] == order_id:
                self.details.load_order(row)
                return

    def _apply_view(self, *_args):
        text = self.search.text().strip()
        if text:
            orders = list(order_repository.search(text))
        else:
            orders = list(order_repository.get_all())

        selected = self.actions.filter.currentData()
        if selected and selected != "all":
            orders = [
                row for row in orders
                if order_badge(row[5], row[4]) == selected
            ]

        self.model.refresh(orders)
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
                    "Ni naročil",
                    "Ustvarite prvo naročilo, da začnete evidenco.",
                )
            self.content_stack.setCurrentIndex(0)
        else:
            self.content_stack.setCurrentIndex(1)

    def _update_status(self, *_args):
        self.status.set_count(self.model.rowCount())
        order_id = self.selected_order()
        if order_id is None:
            self.status.set_selected(None)
            return
        row = self.table.selectionModel().selectedRows()[0].row()
        self.status.set_selected(str(self.model.orders[row][1]))
