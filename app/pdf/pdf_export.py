from __future__ import annotations

import os
import re
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget

from app.core.ui.notify import toast

from app.core.constants import EXPORT_DIR
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.pdf.pdf_company import load_pdf_options
from app.pdf.pdf_engine import PdfDocument, pdf_engine
from app.pdf.upn_qr import format_reference


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "dokument")
    return cleaned.strip("_") or "dokument"


def _items(rows) -> list[dict]:
    items = []
    for row in rows or []:
        items.append({
            "code": row[2] if len(row) > 2 else "",
            "name": row[3] if len(row) > 3 else "",
            "quantity": row[5] if len(row) > 5 else "",
            "price": row[7] if len(row) > 7 else 0,
            "discount": row[8] if len(row) > 8 else 0,
            "vat": row[9] if len(row) > 9 else 0,
            "total": row[10] if len(row) > 10 else 0,
        })
    return items


def _customer(customer_id) -> dict:
    row = customer_repository.get_by_id(customer_id) if customer_id else None
    if not row:
        return {}
    city = " ".join(part for part in (row[4] or "", row[5] or "") if part).strip()
    return {
        "name": row[1] or "",
        "address": row[3] or "",
        "city": city,
        "tax": row[7] or "",
    }


def _output_path(number: str) -> Path:
    from app.core.security import ensure_inside

    options = load_pdf_options()
    folder = Path(options["folder"]) if options.get("folder") else EXPORT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    return ensure_inside(folder / f"{_safe_name(number)}.pdf", folder)


class PdfExport:

    def export_document(self, document: PdfDocument) -> Path:
        from app.core.permissions import audit, require

        require("export")
        path = pdf_engine.render(document, _output_path(document.number))
        audit("export", str(path.name))
        return path

    def export_invoice(self, invoice_id) -> Path:
        invoice = invoice_repository.get_by_id(invoice_id)
        if invoice is None:
            raise ValueError("Račun ne obstaja.")
        status = str(invoice[5] or "")
        if status in ("", "Osnutek"):
            invoice_repository.mark_sent(invoice_id)
            invoice = invoice_repository.get_by_id(invoice_id) or invoice
        customer = _customer(invoice[2])
        return self.export_document(
            PdfDocument(
                doc_type="invoice",
                number=str(invoice[1]),
                issue_date=str(invoice[3] or ""),
                due_date=str(invoice[4] or ""),
                reference=format_reference(str(invoice[1])),
                notes=invoice[10] or "",
                customer_name=customer.get("name", ""),
                customer_address=customer.get("address", ""),
                customer_city=customer.get("city", ""),
                customer_tax=customer.get("tax", ""),
                items=_items(invoice_repository.get_items(invoice_id)),
                subtotal=float(invoice[6] or 0),
                discount=float(invoice[7] or 0),
                vat=float(invoice[8] or 0),
                total=float(invoice[9] or 0),
                status=str(invoice[5] or ""),
                vat_liable=invoice_repository.get_vat_liable(invoice_id),
            )
        )

    def export_offer(self, offer_id) -> Path:
        offer = offer_repository.get_by_id(offer_id)
        if offer is None:
            raise ValueError("Ponudba ne obstaja.")
        customer = _customer(offer[2])
        return self.export_document(
            PdfDocument(
                doc_type="offer",
                number=str(offer[1]),
                issue_date=str(offer[3] or ""),
                due_date=str(offer[4] or ""),
                reference=str(offer[1]),
                notes=offer[10] or "",
                customer_name=customer.get("name", ""),
                customer_address=customer.get("address", ""),
                customer_city=customer.get("city", ""),
                customer_tax=customer.get("tax", ""),
                items=_items(offer_repository.get_items(offer_id)),
                subtotal=float(offer[6] or 0),
                discount=float(offer[7] or 0),
                vat=float(offer[8] or 0),
                total=float(offer[9] or 0),
                vat_liable=offer_repository.get_vat_liable(offer_id),
            )
        )

    def export_order(self, order_id) -> Path:
        return self._export_order_like(order_id, "order")

    def export_delivery(self, order_id) -> Path:
        return self._export_order_like(order_id, "delivery")

    def _export_order_like(self, order_id, doc_type: str) -> Path:
        order = order_repository.get_by_id(order_id)
        if order is None:
            raise ValueError("Naročilo ne obstaja.")
        customer = _customer(order[2])
        number = str(order[1])
        if doc_type == "delivery":
            number = f"DOB-{number}"
        return self.export_document(
            PdfDocument(
                doc_type=doc_type,
                number=number,
                issue_date=str(order[3] or ""),
                due_date=str(order[4] or ""),
                reference=str(order[1]),
                notes=order[10] or "",
                customer_name=customer.get("name", ""),
                customer_address=customer.get("address", ""),
                customer_city=customer.get("city", ""),
                customer_tax=customer.get("tax", ""),
                items=_items(order_repository.get_items(order_id)),
                subtotal=float(order[6] or 0),
                discount=float(order[7] or 0),
                vat=float(order[8] or 0),
                total=float(order[9] or 0),
                vat_liable=order_repository.get_vat_liable(order_id),
            )
        )

    def open_pdf(self, path: Path) -> None:
        """Open in the OS viewer without affecting JU-TAN window lifetime.

        Windows: os.startfile is detached and must never close MainWindow.
        Opening a PDF must never call quit/accept/reject on the app.
        """
        target = Path(path)
        if not target.exists():
            raise FileNotFoundError(f"PDF ne obstaja: {target}")
        if os.name == "nt":
            # Detached ShellExecute — does not transfer Qt ownership or focus quit.
            os.startfile(str(target))  # noqa: S606 — intentional OS file open
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def print_pdf(self, path: Path) -> None:
        from app.core.permissions import audit, require

        require("print")
        audit("print", str(path))
        if os.name == "nt":
            os.startfile(str(path), "print")
            return
        self.open_pdf(path)

    def show_result(self, parent: QWidget | None, path: Path) -> None:
        toast(parent, "PDF ustvarjen")
        self.open_pdf(path)


pdf_export = PdfExport()
