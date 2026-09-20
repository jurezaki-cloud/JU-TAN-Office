from __future__ import annotations

from app.core.permissions import gated
from app.modules.suppliers.suppliers_repository import (
    SUPPLIER_STATUSES,
    suppliers_repository,
)


class SuppliersController:
    def __init__(self, repository=suppliers_repository) -> None:
        self.repository = repository

    def list_rows(self, query: str = "", status: str = "all") -> list:
        rows = self.repository.search(query) if query.strip() else self.repository.get_all()
        if status not in ("all", "", None):
            rows = [row for row in rows if row[6] == status]
        return rows

    def get(self, supplier_id: int):
        return self.repository.get_by_id(supplier_id)

    def statuses(self) -> tuple[str, ...]:
        return SUPPLIER_STATUSES

    @gated("write", "edit")
    def save(self, supplier_id: int | None, data: dict) -> int:
        if supplier_id is None:
            return self.repository.add(
                data["name"],
                data.get("tax_number") or "",
                data.get("contact") or "",
                data.get("phone") or "",
                data.get("email") or "",
                data.get("status") or "Active",
                data.get("notes") or "",
            )
        self.repository.update(
            supplier_id,
            data["name"],
            data.get("tax_number") or "",
            data.get("contact") or "",
            data.get("phone") or "",
            data.get("email") or "",
            data.get("status") or "Active",
            data.get("notes") or "",
        )
        return supplier_id

    @gated("delete", "delete")
    def delete(self, supplier_id: int) -> None:
        self.repository.delete(supplier_id)

    def as_dict(self, supplier_id: int) -> dict | None:
        row = self.repository.get_by_id(supplier_id)
        if row is None:
            return None
        return {
            "id": row[0],
            "name": row[1] or "",
            "tax_number": row[2] or "",
            "contact": row[3] or "",
            "phone": row[4] or "",
            "email": row[5] or "",
            "status": row[6] or "Active",
            "notes": row[7] or "",
        }
