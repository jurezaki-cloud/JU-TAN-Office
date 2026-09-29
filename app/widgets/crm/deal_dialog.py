from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDoubleSpinBox
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.modules.crm.crm_controller import CrmController
from app.widgets.cards.enterprise_card import EnterpriseCard


class DealDialog(EnterpriseDialog):
    def __init__(self, deal_id: int, parent=None, controller=None) -> None:
        super().__init__(
            parent, title="Prodajna priložnost",
            heading="Uredi prodajno priložnost",
            size="MEDIUM", state_key="dialog.crm_deal",
        )
        self.controller = controller or CrmController()
        self.deal_id = deal_id
        self.deal = self.controller.repository.get_deal(deal_id)
        if self.deal is None:
            raise ValueError("Priložnost ne obstaja.")
        self.bind_save(self._accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.title = QLineEdit(str(self.deal[3] or ""))
        self.company = QLineEdit(str(self.deal[4] or ""))
        self.stage = QComboBox()
        stage_labels = {
            "Lead": "Novo", "Qualified": "Kontaktirano", "Proposal": "Ponudba",
            "Negotiation": "Pogajanja", "Won": "Dogovorjeno", "Lost": "Izgubljeno",
        }
        for value in self.controller.stages():
            self.stage.addItem(stage_labels.get(value, value), value)
        self.stage.setCurrentIndex(max(0, self.stage.findData(str(self.deal[5] or "Lead"))))
        self.owner = QComboBox()
        self.owner.setEditable(True)
        self.owner.addItems(self.controller.salespeople())
        self.owner.setCurrentText(str(self.deal[6] or ""))
        self.priority = QComboBox()
        priority_labels = {
            "Low": "Nizka", "Normal": "Normalna", "High": "Visoka", "Urgent": "Nujna",
        }
        for value in self.controller.service.priorities():
            self.priority.addItem(priority_labels.get(value, value), value)
        self.priority.setCurrentIndex(max(0, self.priority.findData(str(self.deal[7] or "Normal"))))
        self.value = QDoubleSpinBox()
        self.value.setMaximum(10_000_000)
        self.value.setDecimals(2)
        self.value.setValue(float(self.deal[8] or 0))

        next_item = self.controller.repository.next_activity(deal_id)
        self.next_due = QDateEdit()
        self.next_due.setDisplayFormat("dd-MM-yyyy")
        self.next_due.setCalendarPopup(True)
        due = str(next_item[6] or "")[:10] if next_item else ""
        parsed = QDate.fromString(due, "yyyy-MM-dd")
        self.next_due.setDate(parsed if parsed.isValid() else QDate.currentDate())
        self.next_title = QLineEdit()
        self.next_title.setPlaceholderText("Dodaj nov naslednji korak")
        self.note = QTextEdit()
        self.note.setAcceptRichText(False)
        self.note.setMaximumHeight(90)

        history = self.controller.repository.stage_history(deal_id)
        history_text = "  •  ".join(
            f"{str(row[4])[:10]}: {row[2] or '—'} → {row[3]}"
            for row in history[:4]
        ) or "Brez premikov med fazami."
        self.history = QLabel(history_text)
        self.history.setWordWrap(True)
        self.history.setObjectName("KpiHint")

        for field in (self.title, self.company, self.next_title):
            field.setObjectName("EnterpriseSearch")
            field.setMinimumHeight(36)
        for field in (self.stage, self.owner, self.priority, self.next_due, self.value):
            field.setObjectName("EnterpriseFilter")
            field.setMinimumHeight(36)

        grid.add("Priložnost", self.title, "Podjetje", self.company)
        grid.add("Faza", self.stage, "Prioriteta", self.priority)
        grid.add("Skrbnik", self.owner, "Vrednost", self.value)
        grid.add("Naslednji korak", self.next_title, "Rok", self.next_due)
        grid.add_full("Nova opomba", self.note)
        card.body.addLayout(grid.layout)
        card.body.addWidget(QLabel("Zadnji premiki"))
        card.body.addWidget(self.history)
        self.body.addWidget(card)

        self.btn_offer = QPushButton("Ustvari ponudbo")
        self.btn_order = QPushButton("Ustvari naročilo")
        self.btn_invoice = QPushButton("Ustvari račun")
        for button in (self.btn_offer, self.btn_order, self.btn_invoice):
            button.setObjectName("SecondaryButton")
            button.setMinimumHeight(36)
        self.btn_offer.clicked.connect(lambda: self._create_document("offer"))
        self.btn_order.clicked.connect(lambda: self._create_document("order"))
        self.btn_invoice.clicked.connect(lambda: self._create_document("invoice"))
        actions = EnterpriseCard("DashboardCard")
        actions.body.addWidget(QLabel("Dokumenti iz priložnosti"))
        self.linked_docs = QLabel()
        self.linked_docs.setObjectName("KpiHint")
        self.linked_docs.setWordWrap(True)
        actions.body.addWidget(self.linked_docs)
        self._refresh_linked_documents()
        actions.body.addWidget(self.btn_offer)
        actions.body.addWidget(self.btn_order)
        actions.body.addWidget(self.btn_invoice)
        self.body.addWidget(actions)

    def _create_document(self, kind: str) -> None:
        customer_id = self.deal[1]
        if not customer_id:
            from app.core.ui.notify import toast
            toast(self, "Priložnost mora biti povezana z obstoječo stranko.")
            return
        if kind == "offer":
            from app.modules.offers.offer_dialog import OfferDialog
            dialog = OfferDialog(self)
        elif kind == "order":
            from app.modules.orders.order_dialog import OrderDialog
            dialog = OrderDialog(self)
        else:
            from app.modules.invoices.invoice_dialog import InvoiceDialog
            dialog = InvoiceDialog(self)
        index = dialog.customer.findData(customer_id)
        if index >= 0:
            dialog.customer.setCurrentIndex(index)
        dialog.notes.setPlainText(
            f"CRM priložnost: {self.title.text().strip()}\n"
            f"Predvidena vrednost: {self.value.value():.2f} EUR"
        )
        if not dialog.exec():
            return
        id_attr = {"offer": "offer_id", "order": "order_id", "invoice": "invoice_id"}[kind]
        document_id = getattr(dialog, id_attr, None)
        if document_id:
            number = dialog.lbl_number.text().strip()
            self.controller.repository.link_document(
                self.deal_id, kind, int(document_id), number
            )
            self._refresh_linked_documents()

    def _refresh_linked_documents(self) -> None:
        labels = {"offer": "Ponudba", "order": "Naročilo", "invoice": "Račun"}
        rows = self.controller.repository.linked_documents(self.deal_id)
        if not rows:
            self.linked_docs.setText("Za to priložnost še ni povezanih dokumentov.")
            return
        self.linked_docs.setText(
            "  •  ".join(
                f"{labels.get(str(row[2]), str(row[2]))}: {row[4] or row[3]}"
                for row in rows[:6]
            )
        )

    def _accept(self) -> None:
        if self.title.text().strip():
            self.accept()

    def data(self) -> dict:
        return {
            "title": self.title.text().strip(),
            "company": self.company.text().strip(),
            "stage": self.stage.currentData(),
            "salesperson": self.owner.currentText().strip(),
            "priority": self.priority.currentData(),
            "value": float(self.value.value()),
        }

    def next_activity_data(self) -> dict | None:
        title = self.next_title.text().strip()
        if not title:
            return None
        return {
            "customer_id": self.deal[1],
            "pipeline_id": self.deal_id,
            "type": "Task",
            "title": title,
            "due_date": self.next_due.date().toString("yyyy-MM-dd"),
            "salesperson": self.owner.currentText().strip(),
            "priority": self.priority.currentData(),
            "notes": "",
        }

    def note_text(self) -> str:
        return self.note.toPlainText().strip()
