from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QWidget,
)

from PySide6.QtCore import QDate, Qt

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.invoice_repository import invoice_repository
from app.database.customer_repository import customer_repository

from app.modules.invoices.models.invoice_items_model import (
    InvoiceItemsModel,
)

from app.modules.invoices.invoice_item_dialog import (
    InvoiceItemDialog,
)
from app.widgets.document_editor import DocumentWorkspace
from app.widgets.invoices.status_badge import invoice_badge


class InvoiceDialog(EnterpriseDialog):

    def __init__(self, parent=None, invoice_id=None):
        from app.core.ui_freeze_diag import span as _diag_span

        with _diag_span("InvoiceDialog.__init__", invoice_id=invoice_id):
            super().__init__(
                parent,
                title="Račun",
                heading="Račun" if invoice_id else "Nov račun",
                size="LARGE",
                state_key="dialog.invoice",
            )
            self.invoice_id = invoice_id
            self.setObjectName("InvoiceDialog")
            self.bind_save(self.save)
            from app.utils.vat import company_vat_liable, parse_vat_liable

            # Snapshot regime at dialog open for new docs; load overwrites for edits.
            self.vat_liable = (
                parse_vat_liable(company_vat_liable()) if invoice_id is None else True
            )

            self.heading.hide()
            self.workspace = DocumentWorkspace(doc_kind="Račun")
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
            self.due_date = QDateEdit()
            self.due_date.setCalendarPopup(True)
            self.due_date.setDate(QDate.currentDate().addDays(30))
            self.notes = QTextEdit()
            self.notes.setAcceptRichText(False)
            self.notes.setMinimumHeight(72)
            self.notes.setMaximumHeight(120)
            self.notes.setObjectName("DocumentNotes")

            grid = FormGrid()
            grid.add("Datum izdaje", self.issue_date, "Rok plačila", self.due_date)
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

            if invoice_id is None:
                self.lbl_number.setText(invoice_repository.get_next_number())
                self.doc_header.set_status("Osnutek", kind="draft")
            self.doc_header.set_document_number(self.lbl_number.text())

            self.btn_add_item.clicked.connect(self.add_item)
            self.btn_remove_item.clicked.connect(self.remove_item)
            self.customer.currentIndexChanged.connect(self._on_customer_changed)
            self.doc_header.save_clicked.connect(self.btn_save.click)
            self.doc_header.export_pdf_clicked.connect(self.export_pdf)
            self.doc_header.more_action.connect(self._on_more_action)

            from app.core.ui.window_state import remember_layout

            remember_layout(
                self,
                "dialog.invoice.workspace",
                splitters=[self.workspace.splitter],
                tables=[self.items_table],
                geometry=False,
            )

            with _diag_span("InvoiceDialog.load_customers"):
                self.load_customers()
            with _diag_span("InvoiceDialog._apply_vat_ui"):
                self._apply_vat_ui()

            if self.invoice_id is not None:
                with _diag_span("InvoiceDialog.load_invoice", invoice_id=self.invoice_id):
                    self.load_invoice()
                with _diag_span("InvoiceDialog._apply_financial_lock", invoice_id=self.invoice_id):
                    self._apply_financial_lock()
            else:
                self._refresh_payment_info()
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

    def _apply_financial_lock(self):
        """Issued financial history is viewable, but paid/cancelled invoices are immutable."""
        invoice = invoice_repository.get_by_id(self.invoice_id)
        if invoice is None:
            return
        status = (invoice[5] or "").strip()
        if status not in ("Plačan", "Storniran"):
            return
        for widget in (
            self.customer, self.issue_date, self.due_date, self.notes,
            self.items_table, self.btn_add_item, self.btn_remove_item,
        ):
            widget.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.doc_header.set_actions_enabled(save=False, export_pdf=True, more=True)

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

        if self.invoice_id is None:
            toast(self, "Najprej shranite račun, nato izvozite PDF.")
            return
        try:
            toast_info(self, "Ustvarjam PDF ...")
            path = pdf_export.export_invoice(self.invoice_id)
            pdf_export.show_result(self, path)
        except Exception as exc:
            QMessageBox.warning(self, "PDF", f"PDF ni bilo mogoče ustvariti:\n{exc}")

    def _refresh_payment_info(self) -> None:
        from app.utils.money import format_eur, money

        if self.invoice_id is None:
            self.totals_panel.set_payment_info("Nov račun — plačila še niso na voljo.")
            return
        try:
            from app.database.payment_repository import payment_repository

            paid = money(payment_repository.sum_for_invoice(self.invoice_id))
            invoice = invoice_repository.get_by_id(self.invoice_id)
            total = money(invoice[9] if invoice else 0)
            remaining = money(total - paid)
            status = invoice_badge(invoice[5] if invoice else None, invoice[4] if invoice else None)
            self.totals_panel.set_payment_info(
                f"Status: {status}\n"
                f"Plačano: {format_eur(paid)} · Preostalo: {format_eur(remaining)}"
            )
            self.doc_header.set_status(status)
        except Exception:
            self.totals_panel.set_payment_info("Plačilne informacije niso na voljo.")

    # =====================================================

    def load_customers(self):

        self.customer.clear()

        customers = customer_repository.get_all()

        for customer in customers:

            self.customer.addItem(
                customer[1],
                customer[0]
            )
        self._on_customer_changed()

    # =====================================================

    def add_item(self):

        dialog = InvoiceItemDialog(self, vat_liable=self.vat_liable)

        if dialog.exec():

            self.items_model.add_item(
                dialog.get_data()
            )

            self.update_total()

    # =====================================================

    def remove_item(self):

        indexes = self.items_table.selectionModel().selectedRows()

        if not indexes:
            return

        self.items_model.remove_row(
            indexes[0].row()
        )

        self.update_total()

    # =====================================================

    def update_total(self):
        from app.utils.money import document_totals, format_eur

        totals = document_totals(self.items_model.items, vat_liable=self.vat_liable)
        self.lbl_subtotal.setText(format_eur(totals["subtotal"]))
        self.lbl_discount.setText(format_eur(totals["discount"]))
        self.lbl_vat.setText(format_eur(totals["vat"]))
        self.lbl_total.setText(format_eur(totals["total"]))
        self.items_panel.set_item_count(len(self.items_model.items))

    # =====================================================
    # SHRANI RAČUN
    # =====================================================
   
    def save(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast
        from app.utils.money import as_float, document_totals, line_gross
        from app.utils.vat import assert_vat_consistent
        import sqlite3
        import time

        if getattr(self, "_saving", False):
            return
        if not allow("write", self):
            return

        if self.customer.currentIndex() == -1:
            toast(self, "Izberite stranko.")
            return

        if len(self.items_model.items) == 0:
            toast(self, "Dodajte vsaj eno postavko.")
            return

        # Normalize line VAT under non-VAT regime before totals/persistence.
        if not self.vat_liable:
            normalized = []
            for row in self.items_model.items:
                row = list(row)
                row[6] = 0
                row[7] = as_float(line_gross(row[2], row[4], 0, row[5], vat_liable=False))
                normalized.append(row)
            self.items_model.refresh(normalized)

        totals = document_totals(self.items_model.items, vat_liable=self.vat_liable)
        subtotal = totals["subtotal"]
        discount = totals["discount"]
        vat_amount = totals["vat"]
        total = totals["total"]

        try:
            assert_vat_consistent(
                vat_liable=self.vat_liable,
                lines=self.items_model.items,
                vat_total=vat_amount,
                show_article_94=not self.vat_liable,
            )
        except ValueError as exc:
            toast(self, str(exc))
            return

        if self.invoice_id is not None:
            from app.database.payment_repository import payment_repository
            from app.utils.money import money
            paid = money(payment_repository.sum_for_invoice(self.invoice_id))
            if money(total) < paid:
                toast(self, "Skupni znesek računa ne sme biti nižji od že prejetih plačil.")
                return

        self._saving = True
        previous_label = self.btn_save.text()
        self.btn_save.setEnabled(False)
        self.btn_save.setText("Shranjujem ...")
        self.doc_header.btn_save.setEnabled(False)
        t0 = time.perf_counter()
        try:
            if self.invoice_id is None:
                invoice_id = None
                last_exc: Exception | None = None
                for _attempt in range(5):
                    number = invoice_repository.get_next_number()
                    self.lbl_number.setText(number)
                    self.doc_header.set_document_number(number)
                    try:
                        invoice_id = invoice_repository.add(
                            invoice_number=number,
                            customer_id=self.customer.currentData(),
                            issue_date=self.issue_date.date().toString("yyyy-MM-dd"),
                            due_date=self.due_date.date().toString("yyyy-MM-dd"),
                            subtotal=subtotal,
                            discount=discount,
                            vat=vat_amount,
                            total=total,
                            notes=self.notes.toPlainText(),
                            status="Izdan",
                            vat_liable=self.vat_liable,
                        )
                        invoice_repository.increase_counter()
                        break
                    except sqlite3.IntegrityError as exc:
                        last_exc = exc
                        # Skip colliding counter slot and retry with healed next number.
                        invoice_repository.increase_counter()
                if invoice_id is None:
                    raise last_exc or RuntimeError("Računa ni bilo mogoče shraniti.")
            else:
                invoice = invoice_repository.get_by_id(self.invoice_id)
                status = invoice[5] if invoice else "Osnutek"

                invoice_repository.update(
                    invoice_id=self.invoice_id,
                    customer_id=self.customer.currentData(),
                    issue_date=self.issue_date.date().toString("yyyy-MM-dd"),
                    due_date=self.due_date.date().toString("yyyy-MM-dd"),
                    subtotal=subtotal,
                    discount=discount,
                    vat=vat_amount,
                    total=total,
                    status=status,
                    notes=self.notes.toPlainText(),
                    vat_liable=self.vat_liable,
                )

                invoice_repository.delete_items(self.invoice_id)
                invoice_id = self.invoice_id

            for row in self.items_model.items:
                qty = row[2]
                price = row[4]
                discount = row[5]
                vat = 0 if not self.vat_liable else row[6]
                invoice_repository.add_item(
                    invoice_id=invoice_id,
                    article_id=row[8],
                    code=row[0],
                    name=row[1],
                    description="",
                    quantity=qty,
                    unit=row[3],
                    price=price,
                    discount=discount,
                    vat=vat,
                    total=as_float(line_gross(qty, price, vat, discount, vat_liable=self.vat_liable)),
                )

            # Editing the amount of an invoice with recorded payments must also
            # refresh its payment-derived status (e.g. paid -> partially paid).
            if self.invoice_id is not None:
                from app.database.payment_repository import payment_repository
                payment_repository.sync_invoice_status(invoice_id, total)

            audit("create" if self.invoice_id is None else "edit", f"invoice:{invoice_id}")
            elapsed_ms = (time.perf_counter() - t0) * 1000
            from app.core.logger import logger
            logger.info("invoice.save id=%s elapsed_ms=%.1f", invoice_id, elapsed_ms)
            self.accept()
        except Exception as exc:
            from app.core.errors import handle_error
            handle_error(exc, context="invoice-save", parent=self)
        finally:
            self._saving = False
            if self.isVisible():
                self.btn_save.setEnabled(True)
                self.btn_save.setText(previous_label)
                self.doc_header.btn_save.setEnabled(True)
    # =====================================================

    def load_invoice(self):

        if self.invoice_id is None:
            return

        invoice = invoice_repository.get_by_id(
            self.invoice_id
        )

        if invoice is None:
            return

        self.vat_liable = invoice_repository.get_vat_liable(self.invoice_id)
        self._apply_vat_ui()

        self.lbl_number.setText(invoice[1])
        self.doc_header.set_document_number(invoice[1])

        index = self.customer.findData(invoice[2])
        if index >= 0:
            self.customer.setCurrentIndex(index)
        self._on_customer_changed()

        self.issue_date.setDate(
            QDate.fromString(invoice[3], "yyyy-MM-dd")
        )

        self.due_date.setDate(
            QDate.fromString(invoice[4], "yyyy-MM-dd")
        )

        self.notes.setPlainText(invoice[10] or "")
        self.doc_header.set_status(invoice_badge(invoice[5], invoice[4]))

        items = invoice_repository.get_items(
            self.invoice_id
        )

        ui_items = []

        for item in items:
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
        self._refresh_payment_info()

    # =====================================================

    def clear(self):

        self.customer.setCurrentIndex(-1)

        self.issue_date.setDate(QDate.currentDate())

        self.due_date.setDate(
            QDate.currentDate().addDays(30)
        )

        self.notes.clear()

        self.items_model.refresh([])

        self.update_total()
        self._on_customer_changed()
        self._refresh_payment_info()
