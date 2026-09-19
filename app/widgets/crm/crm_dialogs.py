from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDoubleSpinBox, QLineEdit, QTextEdit

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.customer_repository import customer_repository
from app.modules.crm.crm_controller import CrmController
from app.widgets.cards.enterprise_card import EnterpriseCard


class LeadDialog(EnterpriseDialog):

    def __init__(self, parent=None, controller: CrmController | None = None) -> None:
        super().__init__(parent, title="Nova priložnost", heading="Nova priložnost", size="MEDIUM", state_key="dialog.lead")
        self.controller = controller or CrmController()
        self.setObjectName("CrmDialog")
        self.bind_save(self._accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.company = QLineEdit()
        self.contact = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.vat = QLineEdit()
        self.title = QLineEdit()
        self.salesperson = QComboBox()
        self.salesperson.setEditable(True)
        self.stage = QComboBox()
        self.priority = QComboBox()
        self.value = QDoubleSpinBox()
        self.value.setMaximum(10_000_000)
        self.value.setDecimals(2)
        for field in (self.company, self.contact, self.email, self.phone, self.vat, self.title):
            field.setObjectName("EnterpriseSearch")
            field.setMinimumHeight(36)
        for combo in (self.salesperson, self.stage, self.priority):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)
        self.value.setObjectName("EnterpriseFilter")
        self.value.setMinimumHeight(36)
        for person in self.controller.salespeople():
            self.salesperson.addItem(person)
        if self.salesperson.count() == 0:
            self.salesperson.addItem(self.controller.service.default_owner())
        self.stage.addItems(list(self.controller.stages()))
        self.priority.addItems(list(self.controller.service.priorities()))
        self.customer = QComboBox()
        self.customer.setObjectName("EnterpriseFilter")
        self.customer.addItem("Nova stranka / lead", None)
        for row in customer_repository.get_all():
            self.customer.addItem(str(row[1]), row[0])
        grid.add("Stranka", self.customer, "Podjetje", self.company)
        grid.add("Kontakt", self.contact, "Email", self.email)
        grid.add("Telefon", self.phone, "DDV / VAT", self.vat)
        grid.add("Naslov deal", self.title, "Skrbnik", self.salesperson)
        grid.add("Stage", self.stage, "Prioriteta", self.priority)
        grid.add("Vrednost", self.value)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)
        self.customer.currentIndexChanged.connect(self._fill_customer)

    def _fill_customer(self) -> None:
        customer_id = self.customer.currentData()
        if not customer_id:
            return
        row = customer_repository.get_by_id(customer_id)
        if row is None:
            return
        self.company.setText(row[1] or "")
        self.contact.setText(row[2] or "")
        self.email.setText(row[8] or "")
        self.phone.setText(row[9] or "")
        self.vat.setText(row[7] or "")

    def _accept(self) -> None:
        if not (self.company.text().strip() or self.title.text().strip()):
            return
        self.accept()

    def data(self) -> dict:
        return {
            "customer_id": self.customer.currentData(),
            "company": self.company.text().strip(),
            "contact": self.contact.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "vat": self.vat.text().strip(),
            "title": self.title.text().strip() or self.company.text().strip(),
            "salesperson": self.salesperson.currentText().strip(),
            "stage": self.stage.currentText(),
            "priority": self.priority.currentText(),
            "value": float(self.value.value()),
        }


class ActivityDialog(EnterpriseDialog):

    def __init__(
        self,
        parent=None,
        controller: CrmController | None = None,
        activity_type: str = "Task",
        customer_id=None,
        pipeline_id=None,
    ) -> None:
        title = "Nova aktivnost" if activity_type != "Meeting" else "Nov sestanek"
        super().__init__(parent, title=title, heading=title, size="SMALL", state_key="dialog.activity")
        self.controller = controller or CrmController()
        self.setObjectName("CrmDialog")
        self.bind_save(self._accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.type = QComboBox()
        self.type.addItems(list(self.controller.service.activity_types()))
        index = self.type.findText(activity_type)
        if index >= 0:
            self.type.setCurrentIndex(index)
        self.title = QLineEdit()
        self.due = QDateEdit()
        self.due.setCalendarPopup(True)
        self.due.setDate(QDate.currentDate())
        self.salesperson = QComboBox()
        self.salesperson.setEditable(True)
        for person in self.controller.salespeople():
            self.salesperson.addItem(person)
        if self.salesperson.count() == 0:
            self.salesperson.addItem(self.controller.service.default_owner())
        self.priority = QComboBox()
        self.priority.addItems(list(self.controller.service.priorities()))
        self.notes = QTextEdit()
        self.notes.setAcceptRichText(False)
        self.notes.setMinimumHeight(72)
        self.notes.setMaximumHeight(120)
        self.customer = QComboBox()
        self.customer.addItem("Brez stranke", None)
        for row in customer_repository.get_all():
            self.customer.addItem(str(row[1]), row[0])
        if customer_id is not None:
            found = self.customer.findData(customer_id)
            if found >= 0:
                self.customer.setCurrentIndex(found)
        self.pipeline_id = pipeline_id
        for combo in (self.type, self.salesperson, self.priority, self.customer):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)
        self.title.setObjectName("EnterpriseSearch")
        self.title.setMinimumHeight(36)
        self.due.setObjectName("EnterpriseFilter")
        self.due.setMinimumHeight(36)
        grid.add("Stranka", self.customer, "Tip", self.type)
        grid.add("Naslov", self.title, "Datum", self.due)
        grid.add("Skrbnik", self.salesperson, "Prioriteta", self.priority)
        grid.add_full("Opomba", self.notes)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

    def _accept(self) -> None:
        if not self.title.text().strip():
            return
        self.accept()

    def data(self) -> dict:
        return {
            "customer_id": self.customer.currentData(),
            "pipeline_id": self.pipeline_id,
            "type": self.type.currentText(),
            "title": self.title.text().strip(),
            "due_date": self.due.date().toString("yyyy-MM-dd"),
            "salesperson": self.salesperson.currentText().strip(),
            "priority": self.priority.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }
