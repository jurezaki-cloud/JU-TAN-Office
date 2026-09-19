from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QTableView,
    QHeaderView,
    QSplitter,
    QMessageBox,
)

from app.modules.customers.models.customer_table_model import CustomerTableModel
from app.modules.customers.customer_dialog import CustomerDialog
from app.modules.customers.customer_details import CustomerDetails
from app.database.repository import customer_repository
from app.widgets.messages import ui_error_boundary


class CustomerPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("CustomerPage")

        layout = QVBoxLayout(self)

        title = QLabel("Stranke")
        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            padding:8px;
        """)
        layout.addWidget(title)

        top_layout = QHBoxLayout()

        self.btn_new = QPushButton("Nova stranka")
        self.btn_edit = QPushButton("Uredi")
        self.btn_delete = QPushButton("Izbriši")
        self.btn_refresh = QPushButton("Osveži")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Išči stranko...")

        self.btn_edit.setProperty("variant", "secondary")\n        self.btn_delete.setProperty("variant", "danger")\n        self.btn_refresh.setProperty("variant", "secondary")\n        top_layout.addWidget(self.btn_new)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_delete)
        top_layout.addWidget(self.btn_refresh)

        top_layout.addStretch()

        top_layout.addWidget(self.search)

        layout.addLayout(top_layout)

        self.table = QTableView()

        self.model = CustomerTableModel([])
        self.table.setModel(self.model)

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)

        self.details = CustomerDetails()

        splitter = QSplitter()

        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setSizes([800, 360])\n        splitter.setChildrenCollapsible(False)

        layout.addWidget(splitter)

        self.search.textChanged.connect(self.search_customer)

        self.btn_new.clicked.connect(self.new_customer)
        self.btn_edit.clicked.connect(self.edit_selected_customer)
        self.btn_delete.clicked.connect(self.delete_selected_customer)
        self.btn_refresh.clicked.connect(self.refresh)

        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(self.edit_customer)
        self.details.editButton.clicked.connect(self.edit_selected_customer)

        self.refresh()

    @ui_error_boundary("Strank ni mogoče naložiti")
    def refresh(self):
        customers = customer_repository.get_all()
        self.model.refresh(customers)

    @ui_error_boundary("Iskanja ni mogoče izvesti")
    def search_customer(self, text):

        text = text.strip()

        if text:
            customers = customer_repository.search(text)
        else:
            customers = customer_repository.get_all()

        self.model.refresh(customers)

    def current_customer_id(self):

        index = self.table.currentIndex()

        if not index.isValid():
            return None

        return self.model.customers[index.row()][0]

    @ui_error_boundary("Podrobnosti ni mogoče prikazati")
    def show_details(self, index):

        customer_id = self.model.customers[index.row()][0]

        customer = customer_repository.get_by_id(customer_id)

        if customer:
            self.details.load_customer(customer)

    @ui_error_boundary("Stranke ni mogoče shraniti")
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

    def edit_selected_customer(self):

        index = self.table.currentIndex()

        if index.isValid():
            self.edit_customer(index)

    @ui_error_boundary("Stranke ni mogoče posodobiti")
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

    @ui_error_boundary("Stranke ni mogoče izbrisati")
    def delete_selected_customer(self):

        customer_id = self.current_customer_id()

        if customer_id is None:
            return

        reply = QMessageBox.question(
            self,
            "Brisanje stranke",
            "Ali res želite izbrisati izbrano stranko?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:

            customer_repository.delete(customer_id)

            self.refresh()
            self.details.clear()
