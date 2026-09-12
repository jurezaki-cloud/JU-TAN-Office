from __future__ import annotations

from pathlib import Path
from typing import Any

from app.excel.excel_export import excel_folders, write_workbook
from app.modules.warehouse.warehouse_service import (
    MOVEMENT_TYPES,
    STATUS_IN_STOCK,
    STATUS_LOW,
    STATUS_OUT,
    StockRow,
    warehouse_service,
)


class WarehouseController:
    def __init__(self, service=warehouse_service) -> None:
        self.service = service

    def kpis(self) -> dict[str, float | int]:
        return self.service.kpis()

    def warehouses(self) -> list[dict[str, str]]:
        return self.service.warehouses()

    def categories(self) -> list[str]:
        return self.service.categories()

    def stock(
        self,
        query: str = "",
        warehouse_id: str = "all",
        status: str = "all",
        category: str = "all",
    ) -> list[StockRow]:
        return self.service.filter_stock(query, warehouse_id, status, category)

    def movements(self) -> list[dict[str, Any]]:
        return self.service.movements()

    def movement_types(self) -> tuple[str, ...]:
        return MOVEMENT_TYPES

    def status_options(self) -> tuple[tuple[str, str], ...]:
        return (
            ("all", "Vsi statusi"),
            (STATUS_IN_STOCK, STATUS_IN_STOCK),
            (STATUS_LOW, STATUS_LOW),
            (STATUS_OUT, STATUS_OUT),
        )

    def default_user(self) -> str:
        return self.service.default_user()

    def add_movement(self, **payload: Any) -> dict[str, Any]:
        return self.service.add_movement(**payload)

    def confirm_inventory(
        self,
        warehouse_id: str,
        counts: list[dict[str, Any]],
        user: str,
        note: str = "",
    ) -> int:
        return self.service.confirm_inventory(warehouse_id, counts, user, note)

    def export_excel(self, path: Path, rows: list[StockRow] | None = None) -> Path:
        headers, data = self.service.export_rows(rows)
        return write_workbook(path, "warehouse", headers, data)

    def export_start_path(self) -> Path:
        return excel_folders()["export"] / "warehouse.xlsx"
