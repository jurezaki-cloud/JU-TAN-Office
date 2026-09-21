from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog
from app.modules.purchase.models.purchase_table_model import PurchaseItemsModel
from app.modules.purchase.purchase_controller import PurchaseController
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.purchase.purchase_table import PurchaseTable


class PurchaseDialog(EnterpriseDialog):

    def __init__(
        self,
        parent=None,
        controller: PurchaseController | None = None,
        purchase_id: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            title="Uredi nabavo" if purchase_id else "Nova nabava",
            heading="Uredi nabavo" if purchase_id else "Nova nabava",
            size="LARGE",
            state_key="dialog.purchase",
        )
        self.controller = controller or PurchaseController()
        self.purchase_id = purchase_id
        self.setObjectName("PurchaseDialog")
        self.bind_save(self.save)

        header_card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.lbl_number = QLabel(self.controller.next_number())
        self.supplier = QComboBox()
        self.supplier.setObjectName("EnterpriseFilter")
        self.supplier.setMinimumHeight(36)
        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setObjectName("EnterpriseFilter")
        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.delivery_date.setObjectName("EnterpriseFilter")
        self.status = QComboBox()
        self.status.setObjectName("EnterpriseFilter")
        self.status.setMinimumHeight(36)
        self.status.addItems(list(self.controller.statuses()))
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)
        grid.add("Številka", self.lbl_number, "Datum", self.issue_date)
        grid.add("Dobavitelj", self.supplier, "Status", self.status)
        grid.add("Rok dobave", self.delivery_date)
        grid.add_full("Opombe", self.notes)
        header_card.body.addLayout(grid.layout)
        self.body.addWidget(header_card)

        items_card = EnterpriseCard("DashboardCard")
        items_title = QLabel("Postavke")
        items_title.setObjectName("DashboardSectionTitle")
        items_card.body.addWidget(items_title)
        self.items_model = PurchaseItemsModel()
        self.items_table = PurchaseTable()
        self.items_table.setModel(self.items_model)
        self.bind_table(self.items_table)
        items_card.body.addWidget(self.items_table)
        toolbar = QHBoxLayout()
        self.btn_add_item = QPushButton("Dodaj postavko")
        self.btn_add_item.setObjectName("SecondaryButton")
        self.btn_remove_item = QPushButton("Odstrani postavko")
        self.btn_remove_item.setObjectName("DangerButton")
        for button in (self.btn_add_item, self.btn_remove_item):
            button.setMinimumHeight(36)
            button.setCursor(Qt.PointingHandCursor)
            toolbar.addWidget(button)
        toolbar.addStretch()
        items_card.body.addLayout(toolbar)
        self.body.addWidget(items_card)

        totals_card = EnterpriseCard("DashboardCard")
        totals_card.body.setContentsMargins(16, 12, 16, 12)
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.lbl_subtotal = QLabel("0.00 €")
        self.lbl_vat = QLabel("0.00 €")
        self.lbl_total = QLabel("0.00 €")
        self.lbl_total.setObjectName("TotalValue")
        total_layout.addWidget(QLabel("Osnova:"))
        total_layout.addWidget(self.lbl_subtotal)
        total_layout.addSpacing(20)
        total_layout.addWidget(QLabel("DDV:"))
        total_layout.addWidget(self.lbl_vat)
        total_layout.addSpacing(20)
        total_layout.addWidget(QLabel("SKUPAJ:"))
        total_layout.addWidget(self.lbl_total)
        totals_card.body.addLayout(total_layout)
        self.body.addWidget(totals_card)

        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_remove_item.clicked.connect(self.remove_item)
        self._load_suppliers()
        if self.purchase_id is not None:
            self._load()

    def _load_suppliers(self) -> None:
        self.supplier.clear()
        for row in self.controller.suppliers():
            self.supplier.addItem(str(row[1]), row[0])

    def add_item(self) -> None:
        dialog = InvoiceItemDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.items_model.add_item({
                "code": data[0],
                "name": data[1],
                "quantity": data[2],
                "price": data[4],
                "vat": data[5],
                "total": data[6],
                "article_id": data[7],
                "qty_received": 0,
            })
            self.update_total()

    def remove_item(self) -> None:
        indexes = self.items_table.selectionModel().selectedRows()
        if not indexes:
            return
        self.items_model.remove_row(indexes[0].row())
        self.update_total()

    def update_total(self) -> None:
        subtotal = 0.0
        vat = 0.0
        for item in self.items_model.items:
            base = float(item.get("quantity") or 0) * float(item.get("price") or 0)
            subtotal += base
            vat += base * float(item.get("vat") or 0) / 100
        self.lbl_subtotal.setText(f"{subtotal:.2f} €")
        self.lbl_vat.setText(f"{vat:.2f} €")
        self.lbl_total.setText(f"{subtotal + vat:.2f} €")

    def save(self) -> None:
        if self.supplier.currentIndex() < 0 or not self.items_model.items:
            return
        subtotal = 0.0
        vat_amount = 0.0
        for item in self.items_model.items:
            base = float(item.get("quantity") or 0) * float(item.get("price") or 0)
            subtotal += base
            vat_amount += base * float(item.get("vat") or 0) / 100
        header = {
            "number": self.lbl_number.text(),
            "supplier_id": self.supplier.currentData(),
            "issue_date": self.issue_date.date().toString("yyyy-MM-dd"),
            "delivery_date": self.delivery_date.date().toString("yyyy-MM-dd"),
            "status": self.status.currentText(),
            "subtotal": subtotal,
            "vat": vat_amount,
            "total": subtotal + vat_amount,
            "notes": self.notes.toPlainText(),
        }
        self.controller.save(self.purchase_id, header, self.items_model.items)
        if header.get("number"):
            self.lbl_number.setText(str(header["number"]))
        self.accept()

    def _load(self) -> None:
        header = self.controller.get(self.purchase_id)
        if header is None:
            return
        self.lbl_number.setText(str(header[1]))
        index = self.supplier.findData(header[2])
        if index >= 0:
            self.supplier.setCurrentIndex(index)
        self.issue_date.setDate(QDate.fromString(str(header[3] or ""), "yyyy-MM-dd"))
        if header[4]:
            self.delivery_date.setDate(QDate.fromString(str(header[4]), "yyyy-MM-dd"))
        status_index = self.status.findText(header[5] or "Draft")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)
        self.notes.setPlainText(header[9] or "")
        items = []
        for item in self.controller.items(self.purchase_id):
            items.append({
                "article_id": item[1],
                "code": item[2],
                "name": item[3],
                "quantity": item[4],
                "qty_received": item[5],
                "price": item[6],
                "vat": item[7],
                "total": item[8],
            })
        self.items_model.refresh(items)
        self.update_total()
