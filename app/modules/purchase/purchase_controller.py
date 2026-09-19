from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.core.permissions import gated
from app.excel.excel_export import excel_folders, write_workbook
from app.modules.purchase.purchase_repository import (
    PURCHASE_STATUSES,
    RECEIVABLE_STATUSES,
    purchase_repository,
)
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import (
    DEFAULT_WAREHOUSE_ID,
    warehouse_service,
)
from app.pdf.pdf_engine import PdfDocument
from app.pdf.pdf_export import pdf_export
from app.pdf.pdf_company import load_company


class PurchaseController:
    def __init__(self, repository=purchase_repository) -> None:
        self.repository = repository

    def list_rows(
        self,
        query: str = "",
        supplier_id: str | int = "all",
        status: str = "all",
        date_filter: str = "all",
        selected_date: str | None = None,
    ) -> list:
        rows = self.repository.search(query) if query.strip() else self.repository.get_all()
        if supplier_id not in ("all", "", None):
            rows = [row for row in rows if int(row[7]) == int(supplier_id)]
        if status not in ("all", "", None):
            rows = [row for row in rows if row[5] == status]
        today = date.today()
        if date_filter == "today":
            rows = [row for row in rows if str(row[3] or "")[:10] == today.isoformat()]
        elif date_filter == "month":
            prefix = today.strftime("%Y-%m")
            rows = [row for row in rows if str(row[3] or "").startswith(prefix)]
        elif date_filter == "day" and selected_date:
            rows = [row for row in rows if str(row[3] or "")[:10] == selected_date]
        return rows

    def get(self, purchase_id: int):
        return self.repository.get_by_id(purchase_id)

    def items(self, purchase_id: int) -> list:
        return self.repository.get_items(purchase_id)

    def statuses(self) -> tuple[str, ...]:
        return PURCHASE_STATUSES

    def suppliers(self) -> list:
        return suppliers_repository.get_all()

    def next_number(self) -> str:
        return self.repository.get_next_number()

    def kpis(self) -> dict:
        return self.repository.kpis()

    @gated("write", "edit")
    def save(self, purchase_id: int | None, header: dict, items: list) -> int:
        if purchase_id is None:
            purchase_id = self.repository.create(
                number=header["number"],
                supplier_id=header["supplier_id"],
                issue_date=header["issue_date"],
                delivery_date=header["delivery_date"],
                status=header["status"],
                subtotal=header["subtotal"],
                vat=header["vat"],
                total=header["total"],
                notes=header.get("notes") or "",
            )
        else:
            self.repository.update(
                purchase_id,
                supplier_id=header["supplier_id"],
                issue_date=header["issue_date"],
                delivery_date=header["delivery_date"],
                status=header["status"],
                subtotal=header["subtotal"],
                vat=header["vat"],
                total=header["total"],
                notes=header.get("notes") or "",
            )
            self.repository.delete_items(purchase_id)
        for row in items:
            self.repository.add_item(
                purchase_id=purchase_id,
                article_id=row.get("article_id"),
                code=row.get("code") or "",
                name=row.get("name") or "",
                quantity=float(row.get("quantity") or 0),
                qty_received=float(row.get("qty_received") or 0),
                price=float(row.get("price") or 0),
                vat=float(row.get("vat") or 0),
                total=float(row.get("total") or 0),
            )
        return purchase_id

    @gated("delete", "delete")
    def delete(self, purchase_id: int) -> None:
        self.repository.delete(purchase_id)

    def can_receive(self, purchase_id: int) -> bool:
        header = self.repository.get_by_id(purchase_id)
        if header is None:
            return False
        return header[5] in RECEIVABLE_STATUSES

    @gated("write", "edit")
    def receive(
        self,
        purchase_id: int,
        receipts: list[dict[str, Any]],
        user: str = "",
    ) -> None:
        header = self.repository.get_by_id(purchase_id)
        if header is None:
            raise ValueError("Nabava ne obstaja.")
        if header[5] == "Cancelled":
            raise ValueError("Preklicane nabave ni mogoče prevzeti.")
        if header[5] == "Received":
            raise ValueError("Nabava je že v celoti prevzeta.")

        company = load_company().name or "JU-TAN"
        number = str(header[1])
        for receipt in receipts:
            qty = float(receipt.get("qty") or 0)
            if qty <= 0:
                continue
            item_id = int(receipt["item_id"])
            current = None
            for item in self.repository.get_items(purchase_id):
                if int(item[0]) == item_id:
                    current = item
                    break
            if current is None:
                continue
            ordered = float(current[4] or 0)
            already = float(current[5] or 0)
            remaining = max(ordered - already, 0)
            qty = min(qty, remaining)
            if qty <= 0:
                continue
            article_id = current[1]
            if article_id:
                warehouse_service.add_movement(
                    movement_type="Prevzem",
                    article_id=int(article_id),
                    warehouse_id=DEFAULT_WAREHOUSE_ID,
                    quantity=qty,
                    user=user or company,
                    note=f"PO {number}",
                )
            self.repository.update_item_received(item_id, already + qty)

        items = self.repository.get_items(purchase_id)
        if items and all(float(item[5] or 0) >= float(item[4] or 0) for item in items):
            status = "Received"
        elif any(float(item[5] or 0) > 0 for item in items):
            status = "Partially Received"
        else:
            status = "Ordered" if header[5] == "Draft" else header[5]
        self.repository.set_status(purchase_id, status, date.today().isoformat())

    def export_excel(self, path: Path, rows: list | None = None) -> Path:
        headers = [
            "Številka", "Dobavitelj", "Datum", "Rok dobave", "Status", "Skupaj",
        ]
        data = []
        for row in rows if rows is not None else self.repository.get_all():
            data.append([row[1], row[2], row[3], row[4], row[5], row[6]])
        return write_workbook(path, "purchase", headers, data)

    def export_start_path(self) -> Path:
        return excel_folders()["export"] / "purchase.xlsx"

    def export_pdf(self, purchase_id: int) -> Path:
        header = self.repository.get_by_id(purchase_id)
        if header is None:
            raise ValueError("Nabava ne obstaja.")
        supplier = suppliers_repository.get_by_id(header[2])
        items = []
        subtotal = float(header[6] or 0)
        vat = float(header[7] or 0)
        total = float(header[8] or 0)
        for item in self.repository.get_items(purchase_id):
            items.append({
                "code": item[2] or "",
                "name": item[3] or "",
                "quantity": item[4],
                "price": item[6],
                "discount": 0,
                "vat": item[7],
                "total": item[8],
            })
        document = PdfDocument(
            doc_type="nabava",
            number=str(header[1]),
            issue_date=str(header[3] or ""),
            due_date=str(header[4] or ""),
            notes=header[9] or "",
            customer_name=(supplier[1] if supplier else ""),
            customer_tax=(supplier[2] if supplier else ""),
            items=items,
            subtotal=subtotal,
            vat=vat,
            total=total,
        )
        return pdf_export.export_document(document)
