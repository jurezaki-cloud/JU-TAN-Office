from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QMessageBox,
    QStackedWidget,
)

from app.core.ui.notify import toast, toast_info
from app.modules.customers.models.customer_table_model import CustomerTableModel
from app.modules.customers.customer_dialog import CustomerDialog
from app.modules.customers.customer_details import CustomerDetails
from app.database.customer_repository import customer_repository
from app.widgets.customers.customer_actions import CustomerActions
from app.widgets.customers.customer_table import CustomerTable
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.customers.search_field import CustomerSearch
from app.widgets.customers.status_bar import CustomerStatusBar
from app.widgets.excel.import_wizard import run_excel_export, run_excel_import


class CustomerPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("CustomerPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Stranke")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        self.actions = CustomerActions()
        self.btn_new = self.actions.btn_new
        self.btn_edit = self.actions.btn_edit
        self.btn_delete = self.actions.btn_delete
        self.btn_refresh = self.actions.btn_refresh

        self.search_field = CustomerSearch()
        self.search = self.search_field.input

        top_layout.addWidget(self.actions)
        top_layout.addStretch()
        top_layout.addWidget(self.search_field)

        layout.addLayout(top_layout)

        self.table = CustomerTable()
        self.model = CustomerTableModel([])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)

        self.details = CustomerDetails()

        splitter = QSplitter()
        splitter.setObjectName("CustomerSplitter")
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setSizes([720, 360])
        splitter.setChildrenCollapsible(False)

        self.empty_state = EmptyStateCard(
            "Ni strank",
            "Dodajte prvo stranko, da začnete evidenco.",
        )

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(splitter)

        layout.addWidget(self.content_stack, 1)

        self.status = CustomerStatusBar()
        layout.addWidget(self.status)

        self.empty_state.action_clicked.connect(self.new_customer)
        from app.core.pagination import IncrementalLoader
        from app.core.ui.debounce import Debouncer
        self._loader = IncrementalLoader(
            lambda offset, size: customer_repository.list_page(
                self.search.text().strip(), limit=size, offset=offset
            )
        )
        self._search_debounced = Debouncer(self.search_customer, 180, self)
        self.search.textChanged.connect(self._search_debounced)

        self.actions.new_clicked.connect(self.new_customer)
        self.actions.edit_clicked.connect(self.edit_selected_customer)
        self.actions.delete_clicked.connect(self.delete_selected_customer)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.excel_clicked.connect(lambda: run_excel_export(self, "customers"))
        self.actions.import_clicked.connect(
            lambda: run_excel_import(self, "customers", self.refresh)
        )
        self.details.editButton.clicked.connect(self.edit_selected_customer)

        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(self.edit_customer)
        self.table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.customers", splitters=[splitter], tables=[self.table], fields=[self.search])
        self.table.verticalScrollBar().valueChanged.connect(self._maybe_more)
        self.refresh()

    def refresh(self):
        self.model.refresh(self._loader.first())
        self._sync_empty_state()
        self._update_status()

    def search_customer(self, text):

        text = (text or "").strip()
        self.model.refresh(self._loader.first())
        self._sync_empty_state()
        self._update_status()

    def _maybe_more(self, value: int) -> None:
        bar = self.table.verticalScrollBar()
        if self._loader.exhausted or value < bar.maximum() - 12:
            return
        self.model.append_rows(self._loader.more())
        self._update_status()

    def current_customer_id(self):

        index = self.table.currentIndex()

        if not index.isValid():
            return None

        return self.model.customers[index.row()][0]

    def show_details(self, index):

        customer_id = self.model.customers[index.row()][0]

        customer = customer_repository.get_by_id(customer_id)

        if customer:
            self.details.load_customer(customer)
        self._update_status()

    def new_customer(self):

        dialog = CustomerDialog(self)

        if dialog.exec():

            data = dialog.get_data()

            if not data["company"]:
                return

            customer_repository.add(
                data["company"],
                data["contact"],
                data["address"],
                data["postal_code"],
                data["city"],
                data["country"],
                data["tax_number"],
                data["email"],
                data["phone"],
            )

            self.refresh()
            toast(self, "Stranka shranjena")

    def edit_selected_customer(self):

        index = self.table.currentIndex()

        if index.isValid():
            self.edit_customer(index)
            return

        toast_info(
            self,
            "Najprej izberi stranko.",
        )

    def edit_customer(self, index):

        customer_id = self.model.customers[index.row()][0]

        customer = customer_repository.get_by_id(customer_id)

        if customer is None:
            return

        customer_dict = {
            "id": customer[0],
            "company": customer[1],
            "contact": customer[2],
            "address": customer[3],
            "postal_code": customer[4],
            "city": customer[5],
            "country": customer[6],
            "tax_number": customer[7],
            "email": customer[8],
            "phone": customer[9],
        }

        dialog = CustomerDialog(self, customer_dict)

        if dialog.exec():

            data = dialog.get_data()

            customer_repository.update(
                customer_id,
                data["company"],
                data["contact"],
                data["address"],
                data["postal_code"],
                data["city"],
                data["country"],
                data["tax_number"],
                data["email"],
                data["phone"],
            )

            self.refresh()

            customer = customer_repository.get_by_id(customer_id)

            if customer:
                self.details.load_customer(customer)
            toast(self, "Stranka shranjena")

    def delete_selected_customer(self):

        customer_id = self.current_customer_id()

        if customer_id is None:
            toast_info(
                self,
                "Najprej izberi stranko.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Brisanje stranke",
            "Ali res želite izbrisati izbrano stranko?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:

            customer_repository.delete(customer_id)
            self.details.clear()
            self.refresh()
            toast(self, "Stranka izbrisana")

    def _sync_empty_state(self):
        if self.model.rowCount() == 0:
            if self.search.text().strip():
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskalnim nizom.",
                )
            else:
                self.empty_state.set_message(
                    "Ni strank",
                    "Dodajte prvo stranko, da začnete evidenco.",
                )
            self.content_stack.setCurrentWidget(self.empty_state)
        else:
            self.content_stack.setCurrentIndex(1)

    def _on_selection_changed(self, *_args):
        self._update_status()

    def _update_status(self):
        self.status.set_count(self.model.rowCount())
        index = self.table.currentIndex()
        if index.isValid() and self.model.customers:
            name = self.model.customers[index.row()][1]
            self.status.set_selected(str(name or ""))
        else:
            self.status.set_selected(None)
