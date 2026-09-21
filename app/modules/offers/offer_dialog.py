from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QMessageBox,
    QTextEdit,
    QWidget,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.customer_repository import customer_repository
from app.database.offer_repository import offer_repository
from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog
from app.modules.invoices.models.invoice_items_model import InvoiceItemsModel
from app.services.numbering_service import numbering_service
from app.widgets.document_editor import DocumentWorkspace


class OfferDialog(EnterpriseDialog):

    def __init__(self, parent=None, offer_id=None, read_only=False):
        super().__init__(
            parent,
            title="Ponudba",
            heading=(
                "Pregled ponudbe"
                if read_only
                else ("Uredi ponudbo" if offer_id else "Nova ponudba")
            ),
            size="LARGE",
            state_key="dialog.offer",
        )
        self.offer_id = offer_id
        self.read_only = bool(read_only)
        self.setObjectName("OfferDialog")
        self.bind_save(self.save)
        from app.utils.vat import company_vat_liable, parse_vat_liable

        self.vat_liable = (
            parse_vat_liable(company_vat_liable()) if offer_id is None else True
        )

        self.heading.hide()
        self.workspace = DocumentWorkspace(doc_kind="Ponudba")
        self.body.addWidget(self.workspace, 1)

        self.doc_header = self.workspace.header
        self.customer_panel = self.workspace.customer_panel
        self.items_panel = self.workspace.items_panel
        self.totals_panel = self.workspace.totals_panel

        self.lbl_number = self.doc_header.lbl_number
        self.customer = self.customer_panel.customer
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
        self.notes.setObjectName("DocumentNotes")

        grid = FormGrid()
        grid.add("Datum", self.issue_date, "Status", self.status)
        grid.add("Velja do", self.valid_until)
        meta_wrap = QWidget()
        meta_wrap.setLayout(grid.layout)
        self.customer_panel.meta_layout.addWidget(meta_wrap)
        self.customer_panel.notes_layout.addWidget(self.notes)

        self.items_model = InvoiceItemsModel()
        self.items_table = self.items_panel.items_table
        self.items_table.setModel(self.items_model)
        self.bind_table(self.items_table)
        self.btn_add_item = self.items_panel.btn_add_item
        self.btn_remove_item = self.items_panel.btn_remove_item

        self.lbl_subtotal = self.totals_panel.lbl_subtotal
        self.lbl_discount = self.totals_panel.lbl_discount
        self.lbl_vat = self.totals_panel.lbl_vat
        self.lbl_vat_caption = self.totals_panel.lbl_vat_caption
        self.lbl_total = self.totals_panel.lbl_total
        self.lbl_vat_notice = self.totals_panel.lbl_vat_notice

        if offer_id is None:
            self.lbl_number.setText(numbering_service.next_offer_number())
        self.doc_header.set_document_number(self.lbl_number.text())
        self.doc_header.set_status(self.status.currentText())
        self.totals_panel.set_payment_info("Ponudba — plačilne informacije po pretvorbi v račun.")

        self.btn_add_item.clicked.connect(self.add_item)
        self.btn_remove_item.clicked.connect(self.remove_item)
        self.customer.currentIndexChanged.connect(self._on_customer_changed)
        self.status.currentTextChanged.connect(lambda text: self.doc_header.set_status(text))
        self.doc_header.save_clicked.connect(self.btn_save.click)
        self.doc_header.export_pdf_clicked.connect(self.export_pdf)
        self.doc_header.more_action.connect(self._on_more_action)

        from app.core.ui.window_state import remember_layout

        remember_layout(
            self,
            "dialog.offer.workspace",
            splitters=[self.workspace.splitter],
            tables=[self.items_table],
            geometry=False,
        )

        self.load_customers()
        self._apply_vat_ui()
        if self.offer_id is not None:
            self.load_offer()
            from app.services.offer_service import offer_service

            if self.read_only or offer_service.is_converted(self.offer_id):
                self.read_only = True
                self._apply_read_only()
        else:
            self.update_total()

    def _apply_vat_ui(self):
        from app.utils.vat import ARTICLE_94_NOTICE, parse_vat_liable

        self.vat_liable = parse_vat_liable(self.vat_liable)
        show_vat = self.vat_liable
        self.lbl_vat_caption.setVisible(show_vat)
        self.lbl_vat.setVisible(show_vat)
        if hasattr(self, "items_table"):
            self.items_table.setColumnHidden(6, not show_vat)
        if show_vat:
            self.lbl_vat_notice.hide()
            self.lbl_vat_notice.clear()
        else:
            self.lbl_vat_notice.setText(ARTICLE_94_NOTICE)
            self.lbl_vat_notice.show()

    def _apply_read_only(self):
        for widget in (
            self.customer,
            self.issue_date,
            self.valid_until,
            self.status,
            self.notes,
            self.items_table,
            self.btn_add_item,
            self.btn_remove_item,
        ):
            widget.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.doc_header.set_actions_enabled(save=False, export_pdf=True, more=True)
        self.setWindowTitle("Pregled ponudbe")

    def _on_customer_changed(self, _index: int = -1) -> None:
        customer_id = self.customer.currentData()
        name = self.customer.currentText()
        self.doc_header.set_customer_name(name if customer_id is not None else None)
        if customer_id is None:
            self.customer_panel.set_customer_record(None)
            return
        self.customer_panel.set_customer_record(customer_repository.get_by_id(customer_id))

    def _on_more_action(self, action: str) -> None:
        if action == "refresh_totals":
            self.update_total()
        elif action == "focus_items":
            self.items_table.setFocus(Qt.OtherFocusReason)
        elif action == "close":
            self.reject()

    def export_pdf(self) -> None:
        from app.core.ui.notify import toast, toast_info
        from app.pdf.pdf_export import pdf_export

        if self.offer_id is None:
            toast(self, "Najprej shranite ponudbo, nato izvozite PDF.")
            return
        try:
            toast_info(self, "Ustvarjam PDF ...")
            path = pdf_export.export_offer(self.offer_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", f"PDF ni bilo mogoče ustvariti:\n{exc}")

    def load_customers(self):
        self.customer.clear()
        for customer in customer_repository.get_all():
            self.customer.addItem(customer[1], customer[0])
        self._on_customer_changed()

    def add_item(self):
        dialog = InvoiceItemDialog(self, vat_liable=self.vat_liable)
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

        totals = document_totals(self.items_model.items, vat_liable=self.vat_liable)
        self.lbl_subtotal.setText(format_eur(totals["subtotal"]))
        self.lbl_discount.setText(format_eur(totals["discount"]))
        self.lbl_vat.setText(format_eur(totals["vat"]))
        self.lbl_total.setText(format_eur(totals["total"]))
        self.items_panel.set_item_count(len(self.items_model.items))

    def save(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast
        from app.services.offer_service import offer_service
        from app.utils.money import as_float, document_totals, line_gross
        from app.utils.vat import assert_vat_consistent

        if self.read_only:
            toast(self, "Ponudba je samo za ogled.")
            return
        if not allow("write", self):
            return
        if self.offer_id is not None and offer_service.is_converted(self.offer_id):
            toast(self, "Ponudba je že pretvorjena v račun in je ni mogoče spreminjati.")
            return
        if self.customer.currentIndex() == -1:
            toast(self, "Izberite stranko.")
            return
        if len(self.items_model.items) == 0:
            toast(self, "Dodajte vsaj eno postavko.")
            return

        if not self.vat_liable:
            normalized = []
            for row in self.items_model.items:
                row = list(row)
                row[6] = 0
                row[7] = as_float(line_gross(row[2], row[4], 0, row[5], vat_liable=False))
                normalized.append(row)
            self.items_model.refresh(normalized)

        totals = document_totals(self.items_model.items, vat_liable=self.vat_liable)
        try:
            assert_vat_consistent(
                vat_liable=self.vat_liable,
                lines=self.items_model.items,
                vat_total=totals["vat"],
                show_article_94=not self.vat_liable,
            )
        except ValueError as exc:
            toast(self, str(exc))
            return

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
            vat_liable=self.vat_liable,
        )

        try:
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
                vat = 0 if not self.vat_liable else row[6]
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
                    vat=vat,
                    total=as_float(
                        line_gross(row[2], row[4], vat, row[5], vat_liable=self.vat_liable)
                    ),
                )
        except ValueError as exc:
            toast(self, str(exc))
            return

        audit("create" if self.offer_id is None else "edit", f"offer:{offer_id}")
        self.accept()

    def load_offer(self):
        offer = offer_repository.get_by_id(self.offer_id)
        if offer is None:
            return

        self.vat_liable = offer_repository.get_vat_liable(self.offer_id)
        self._apply_vat_ui()

        self.lbl_number.setText(offer[1])
        self.doc_header.set_document_number(offer[1])
        index = self.customer.findData(offer[2])
        if index >= 0:
            self.customer.setCurrentIndex(index)
        self._on_customer_changed()

        self.issue_date.setDate(QDate.fromString(offer[3], "yyyy-MM-dd"))
        if offer[4]:
            self.valid_until.setDate(QDate.fromString(offer[4], "yyyy-MM-dd"))

        status_index = self.status.findText(offer[5] or "Osnutek")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)
        self.doc_header.set_status(self.status.currentText())

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
        self.totals_panel.set_payment_info(
            f"Status ponudbe: {self.status.currentText()}\n"
            f"Velja do: {self.valid_until.date().toString('dd.MM.yyyy')}"
        )
