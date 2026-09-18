from PySide6.QtWidgets import (
    QHeaderView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.database.offer_repository import offer_repository
from app.database.repository import customer_repository
from app.database.article_repository import article_repository
from app.database.invoice_repository import invoice_repository
from app.database.settings_repository import settings_repository
from app.invoices.dialogs import InvoiceDatesDialog
from app.offers.models.offer_table_model import OfferTableModel
from app.offers.offer_details import OfferDetails
from app.offers.offer_dialog import OfferDialog
from app.services.numbering_service import numbering_service
from app.services.offer_pdf import generate_offer_pdf
from app.widgets.messages import show_error


class Offers(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("OffersPage")

        layout = QVBoxLayout(self)
        title = QLabel("Ponudbe")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:8px;")
        layout.addWidget(title)

        actions = QHBoxLayout()
        self.btn_new = QPushButton("➕ Nova ponudba")
        self.btn_edit = QPushButton("✏️ Uredi")
        self.btn_delete = QPushButton("🗑 Izbriši")
        self.btn_refresh = QPushButton("🔄 Osveži")
        self.btn_pdf = QPushButton("📄 Izvozi PDF")
        self.btn_invoice = QPushButton("🧾 Pretvori v račun")
        for button in (
            self.btn_new, self.btn_edit, self.btn_delete, self.btn_refresh,
            self.btn_pdf, self.btn_invoice,
        ):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableView()
        self.model = OfferTableModel([])
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.details = OfferDetails()
        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setSizes([760, 320])
        layout.addWidget(splitter)

        self.btn_new.clicked.connect(self.new_offer)
        self.btn_edit.clicked.connect(self.edit_selected_offer)
        self.btn_delete.clicked.connect(self.delete_selected_offer)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_invoice.clicked.connect(self.convert_to_invoice)
        self.table.clicked.connect(self.show_details)
        self.table.doubleClicked.connect(self.edit_offer)
        self.details.editButton.clicked.connect(self.edit_selected_offer)
        self.details.deleteButton.clicked.connect(self.delete_selected_offer)
        self.refresh()

    def refresh(self):
        try:
            self.model.refresh(offer_repository.get_all())
            self.details.clear()
        except Exception as error:
            show_error(self, error, "Ponudb ni mogoče naložiti")

    def current_offer_id(self):
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        return self.model.offers[index.row()][0]

    def show_details(self, index):
        self.details.load_offer(self.model.offers[index.row()])

    def new_offer(self):
        try:
            customers = customer_repository.get_all()
            if not customers:
                QMessageBox.information(
                    self,
                    "Manjka stranka",
                    "Pred prvo ponudbo ustvarite vsaj eno stranko.",
                )
                return
            number = numbering_service.preview_offer_number()
            dialog = OfferDialog(
                customers, article_repository.get_all(), number, self
            )
            if not dialog.exec():
                return
            data = dialog.get_data()
            data["number"] = numbering_service.next_offer_number()
            offer_repository.create_with_items(
                data["number"], data["customer_id"], data["issue_date"],
                data["valid_until"], data["status"], data["notes"],
                data["items"],
            )
            self.refresh()
        except Exception as error:
            show_error(self, error, "Ponudbe ni mogoče shraniti")

    def edit_selected_offer(self):
        offer_id = self.current_offer_id() or self.details.offer_id
        if offer_id is None:
            QMessageBox.information(self, "Urejanje", "Najprej izberite ponudbo.")
            return
        self.edit_offer_by_id(offer_id)

    def edit_offer(self, index):
        self.edit_offer_by_id(self.model.offers[index.row()][0])

    def edit_offer_by_id(self, offer_id):
        try:
            offer = offer_repository.get_by_id(offer_id)
            if offer is None:
                raise LookupError("Ponudba ne obstaja.")
            dialog = OfferDialog(
                customer_repository.get_all(), article_repository.get_all(),
                offer[1], self, offer, self._items_as_dicts(offer_id),
            )
            if not dialog.exec():
                return
            data = dialog.get_data()
            offer_repository.update_with_items(
                offer_id, data["customer_id"], data["issue_date"],
                data["valid_until"], data["status"], data["notes"],
                data["items"],
            )
            self.refresh()
        except Exception as error:
            show_error(self, error, "Ponudbe ni mogoče posodobiti")

    @staticmethod
    def _items_as_dicts(offer_id):
        return [
            {
                "id": row[0], "article_id": row[1], "code": row[2] or "",
                "name": row[3] or "", "description": row[4] or "",
                "quantity": row[5], "unit": row[6] or "", "price": row[7],
                "discount": row[8], "vat": row[9], "total": row[10],
            }
            for row in offer_repository.get_items(offer_id)
        ]

    def delete_selected_offer(self):
        offer_id = self.current_offer_id() or self.details.offer_id
        if offer_id is None:
            QMessageBox.information(self, "Brisanje", "Najprej izberite ponudbo.")
            return
        reply = QMessageBox.question(
            self,
            "Brisanje ponudbe",
            "Ali res želite izbrisati izbrano ponudbo in vse njene postavke?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            offer_repository.delete(offer_id)
            self.refresh()
        except Exception as error:
            show_error(self, error, "Ponudbe ni mogoče izbrisati")

    def export_pdf(self):
        offer_id = self.current_offer_id() or self.details.offer_id
        if offer_id is None:
            QMessageBox.information(self, "PDF", "Najprej izberite ponudbo.")
            return
        try:
            offer = offer_repository.get_by_id(offer_id)
            if offer is None:
                raise LookupError("Ponudba ne obstaja.")
            customer = customer_repository.get_by_id(offer[2])
            items = offer_repository.get_items(offer_id)
            suggested = f"Ponudba-{offer[1]}.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, "Shrani ponudbo PDF", suggested, "PDF dokumenti (*.pdf)"
            )
            if not path:
                return
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            generate_offer_pdf(
                path, offer, customer, items, settings_repository.get()
            )
            QMessageBox.information(self, "PDF", "Ponudba je uspešno izvožena.")
        except Exception as error:
            show_error(self, error, "PDF-ja ni mogoče ustvariti")

    def convert_to_invoice(self):
        offer_id = self.current_offer_id() or self.details.offer_id
        if offer_id is None:
            QMessageBox.information(self, "Račun", "Najprej izberite ponudbo.")
            return
        dialog = InvoiceDatesDialog(
            self, settings_repository.get()["payment_terms_days"]
        )
        if not dialog.exec():
            return
        try:
            issue_date, due_date = dialog.get_data()
            invoice_id = invoice_repository.create_from_offer(
                offer_id, issue_date, due_date
            )
            invoice = invoice_repository.get_by_id(invoice_id)
            QMessageBox.information(
                self, "Račun ustvarjen",
                f"Ponudba je pretvorjena v račun {invoice[1]}.",
            )
        except Exception as error:
            show_error(self, error, "Ponudbe ni mogoče pretvoriti v račun")
