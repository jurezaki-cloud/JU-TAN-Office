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
from app.database.customer_repository import customer_repository
from app.database.offer_repository import offer_repository
from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog
from app.modules.invoices.models.invoice_items_model import InvoiceItemsModel
from app.services.numbering_service import numbering_service
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.invoices.invoice_table import InvoiceTable


class OfferDialog(EnterpriseDialog):

    def __init__(self, parent=None, offer_id=None):
        super().__init__(
            parent,
            title="Ponudba",
            heading="Uredi ponudbo" if offer_id else "Nova ponudba",
            size="LARGE",
            state_key="dialog.offer",
        )
        self.offer_id = offer_id
        self.setObjectName("OfferDialog")
        self.bind_save(self.save)

        header_card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.lbl_number = QLabel(numbering_service.next_offer_number())
        self.customer = QComboBox()
        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDate(QDate.currentDate())
        self.valid_until = QDateEdit()
        self.valid_until.setCalendarPopup(True)
        self.valid_until.setDate(QDate.currentDate().addDays(14))
        self.status = QComboBox()
        self.status.addItems(["Osnutek", "Poslana", "Sprejeta", "Zavrnjena"])
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)
        grid.add("Številka", self.lbl_number, "Datum", self.issue_date)
        grid.add("Stranka", self.customer, "Status", self.status)
        grid.add("Velja do", self.valid_until)
        grid.add_full("Opombe", self.notes)
        header_card.body.addLayout(grid.layout)
        self.body.addWidget(header_card)

        items_card = EnterpriseCard("DashboardCard")
        items_title = QLabel("Postavke")
        items_title.setObjectName("DashboardSectionTitle")
        items_card.body.addWidget(items_title)
        self.items_model = InvoiceItemsModel()
        self.items_table = InvoiceTable()
        self.items_table.setModel(self.items_model)
        self.bind_table(self.items_table)
        items_card.body.addWidget(self.items_table)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
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
        self.load_customers()
        if self.offer_id is not None:
            self.load_offer()

    def load_customers(self):
        self.customer.clear()
        for customer in customer_repository.get_all():
            self.customer.addItem(customer[1], customer[0])

    def add_item(self):
        dialog = InvoiceItemDialog(self)
        if dialog.exec():
            self.items_model.add_item(dialog.get_data())
            self.update_total()

    def remove_item(self):
        indexes = self.items_table.selectionModel().selectedRows()
        if not indexes:
            return
        self.items_model.remove_row(indexes[0].row())
        self.update_total()

    def update_total(self):
        from app.utils.money import document_totals, format_eur

        totals = document_totals(self.items_model.items)
        self.lbl_subtotal.setText(format_eur(totals["subtotal"]))
        self.lbl_vat.setText(format_eur(totals["vat"]))
        self.lbl_total.setText(format_eur(totals["total"]))

    def save(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast
        from app.utils.money import as_float, document_totals, line_gross

        if not allow("write", self):
            return
        if self.customer.currentIndex() == -1:
            toast(self, "Izberite stranko.")
            return
        if len(self.items_model.items) == 0:
            toast(self, "Dodajte vsaj eno postavko.")
            return

        totals = document_totals(self.items_model.items)
        payload = dict(
            customer_id=self.customer.currentData(),
            issue_date=self.issue_date.date().toString("yyyy-MM-dd"),
            valid_until=self.valid_until.date().toString("yyyy-MM-dd"),
            status=self.status.currentText(),
            subtotal=totals["subtotal"],
            discount=totals["discount"],
            vat=totals["vat"],
            total=totals["total"],
            notes=self.notes.toPlainText(),
        )

        if self.offer_id is None:
            offer_id = offer_repository.create(
                number=self.lbl_number.text(),
                **payload,
            )
        else:
            offer_repository.update(self.offer_id, **payload)
            offer_repository.delete_items(self.offer_id)
            offer_id = self.offer_id

        for row in self.items_model.items:
            offer_repository.add_item(
                offer_id=offer_id,
                article_id=row[8],
                code=row[0],
                name=row[1],
                description="",
                quantity=row[2],
                unit=row[3],
                price=row[4],
                discount=row[5],
                vat=row[6],
                total=as_float(line_gross(row[2], row[4], row[6], row[5])),
            )

        audit("create" if self.offer_id is None else "edit", f"offer:{offer_id}")
        self.accept()

    def load_offer(self):
        offer = offer_repository.get_by_id(self.offer_id)
        if offer is None:
            return

        self.lbl_number.setText(offer[1])
        index = self.customer.findData(offer[2])
        if index >= 0:
            self.customer.setCurrentIndex(index)

        self.issue_date.setDate(QDate.fromString(offer[3], "yyyy-MM-dd"))
        if offer[4]:
            self.valid_until.setDate(QDate.fromString(offer[4], "yyyy-MM-dd"))

        status_index = self.status.findText(offer[5] or "Osnutek")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)

        self.notes.setPlainText(offer[10] or "")

        ui_items = []
        for item in offer_repository.get_items(self.offer_id):
            ui_items.append([
                item[2],
                item[3],
                item[5],
                item[6],
                item[7],
                item[8] or 0,
                item[9],
                item[10],
                item[1],
            ])
        self.items_model.refresh(ui_items)
        self.update_total()
