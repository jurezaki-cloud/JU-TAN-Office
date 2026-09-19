from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.constants import DATA_DIR
from app.database.article_repository import article_repository
from app.pdf.pdf_company import load_company

STORE_PATH = DATA_DIR / "warehouse.json"

DEFAULT_WAREHOUSE_ID = "main"
DEFAULT_WAREHOUSE_NAME = "Glavno skladišče"

MOVEMENT_TYPES = (
    "Prevzem",
    "Izdaja",
    "Korekcija",
    "Inventura",
    "Rezervacija",
)

STATUS_IN_STOCK = "🟢 Na zalogi"
STATUS_LOW = "🟡 Nizka zaloga"
STATUS_OUT = "🔴 Ni zaloge"


@dataclass(frozen=True)
class StockRow:
    article_id: int
    code: str
    name: str
    warehouse_id: str
    warehouse: str
    qty: float
    reserved: float
    free: float
    min_qty: float
    status: str
    category: str
    price: float

    @property
    def value(self) -> float:
        return max(self.qty, 0.0) * float(self.price or 0)


def stock_status(qty: float, min_qty: float) -> str:
    if qty <= 0:
        return STATUS_OUT
    if min_qty > 0 and qty <= min_qty:
        return STATUS_LOW
    return STATUS_IN_STOCK


class WarehouseService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or STORE_PATH

    def warehouses(self) -> list[dict[str, str]]:
        return list(self._load()["warehouses"])

    def warehouse_name(self, warehouse_id: str) -> str:
        for item in self.warehouses():
            if item["id"] == warehouse_id:
                return item["name"]
        return DEFAULT_WAREHOUSE_NAME

    def categories(self) -> list[str]:
        units = {
            str(row[3] or "").strip()
            for row in article_repository.get_all()
            if str(row[3] or "").strip()
        }
        return sorted(units, key=str.casefold)

    def stock_rows(self) -> list[StockRow]:
        data = self._load()
        warehouses = {item["id"]: item["name"] for item in data["warehouses"]}
        stock = data.get("stock") or {}
        rows: list[StockRow] = []
        for article in article_repository.get_all():
            article_id = int(article[0])
            overlay = stock.get(str(article_id)) or {}
            targets = overlay or {DEFAULT_WAREHOUSE_ID: {}}
            for warehouse_id, cell in targets.items():
                qty = _num(cell.get("qty"))
                reserved = _num(cell.get("reserved"))
                min_qty = _num(cell.get("min_qty"))
                rows.append(
                    StockRow(
                        article_id=article_id,
                        code=str(article[1] or ""),
                        name=str(article[2] or ""),
                        warehouse_id=warehouse_id,
                        warehouse=warehouses.get(warehouse_id, warehouse_id),
                        qty=qty,
                        reserved=reserved,
                        free=max(qty - reserved, 0.0),
                        min_qty=min_qty,
                        status=stock_status(qty, min_qty),
                        category=str(article[3] or ""),
                        price=_num(article[4]),
                    )
                )
        rows.sort(key=lambda row: (row.name.casefold(), row.warehouse.casefold()))
        return rows

    def filter_stock(
        self,
        query: str = "",
        warehouse_id: str = "all",
        status: str = "all",
        category: str = "all",
    ) -> list[StockRow]:
        text = query.strip().casefold()
        filtered: list[StockRow] = []
        for row in self.stock_rows():
            if warehouse_id not in ("all", "", None) and row.warehouse_id != warehouse_id:
                continue
            if status not in ("all", "", None) and row.status != status:
                continue
            if category not in ("all", "", None) and row.category != category:
                continue
            haystack = f"{row.code} {row.name} {row.warehouse} {row.category}".casefold()
            if text and text not in haystack:
                continue
            filtered.append(row)
        return filtered

    def kpis(self) -> dict[str, float | int]:
        rows = self.stock_rows()
        seen: set[int] = set()
        in_stock: set[int] = set()
        low: set[int] = set()
        reserved: set[int] = set()
        value = 0.0
        for row in rows:
            seen.add(row.article_id)
            if row.qty > 0:
                in_stock.add(row.article_id)
            if row.min_qty > 0 and row.qty <= row.min_qty:
                low.add(row.article_id)
            if row.reserved > 0:
                reserved.add(row.article_id)
            value += row.value
        return {
            "articles": len(seen),
            "in_stock": len(in_stock),
            "low_stock": len(low),
            "reserved": len(reserved),
            "value": value,
        }

    def movements(self) -> list[dict[str, Any]]:
        items = list(self._load().get("movements") or [])
        items.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
        return items

    def add_movement(
        self,
        *,
        movement_type: str,
        article_id: int,
        warehouse_id: str,
        quantity: float,
        user: str,
        note: str = "",
        min_qty: float | None = None,
        counted: float | None = None,
    ) -> dict[str, Any]:
        from app.core.permissions import audit, require

        require("write")
        if movement_type not in MOVEMENT_TYPES:
            raise ValueError("Neznana vrsta gibanja.")
        article = article_repository.get_by_id(article_id)
        if article is None:
            raise ValueError("Artikel ne obstaja.")
        data = self._load()
        cell = self._cell(data, article_id, warehouse_id)
        qty = _num(cell.get("qty"))
        reserved = _num(cell.get("reserved"))
        amount = _num(quantity)

        if movement_type == "Prevzem":
            cell["qty"] = qty + abs(amount)
        elif movement_type == "Izdaja":
            cell["qty"] = qty - abs(amount)
        elif movement_type == "Korekcija":
            cell["qty"] = qty + amount
        elif movement_type == "Inventura":
            target = amount if counted is None else _num(counted)
            cell["qty"] = target
            amount = target - qty
        elif movement_type == "Rezervacija":
            cell["reserved"] = max(reserved + amount, 0.0)

        if min_qty is not None:
            cell["min_qty"] = max(_num(min_qty), 0.0)

        movement = {
            "id": self._next_id(data),
            "date": datetime.now().isoformat(timespec="seconds"),
            "type": movement_type,
            "article_id": article_id,
            "article_code": str(article[1] or ""),
            "article_name": str(article[2] or article[1] or ""),
            "warehouse_id": warehouse_id,
            "quantity": amount,
            "user": (user or load_company().name or "JU-TAN").strip(),
            "note": (note or "").strip(),
        }
        data.setdefault("movements", []).append(movement)
        self._save(data)
        audit("create", f"warehouse:{movement['id']}")
        return movement

    def confirm_inventory(
        self,
        warehouse_id: str,
        counts: list[dict[str, Any]],
        user: str,
        note: str = "",
    ) -> int:
        from app.core.permissions import require

        require("write")
        applied = 0
        for item in counts:
            counted = _num(item.get("counted"))
            current = _num(item.get("qty"))
            if counted == current:
                continue
            self.add_movement(
                movement_type="Inventura",
                article_id=int(item["article_id"]),
                warehouse_id=warehouse_id,
                quantity=counted - current,
                user=user,
                note=note or "Inventura",
                counted=counted,
                min_qty=item.get("min_qty"),
            )
            applied += 1
        return applied

    def export_rows(self, rows: list[StockRow] | None = None) -> tuple[list[str], list[list]]:
        headers = [
            "Šifra",
            "Naziv",
            "Skladišče",
            "Na zalogi",
            "Rezervirano",
            "Prosto",
            "Minimalna zaloga",
            "Status",
            "Kategorija",
        ]
        data = []
        for row in rows if rows is not None else self.stock_rows():
            data.append([
                row.code,
                row.name,
                row.warehouse,
                row.qty,
                row.reserved,
                row.free,
                row.min_qty,
                row.status,
                row.category,
            ])
        return headers, data

    def default_user(self) -> str:
        return (load_company().name or "JU-TAN").strip()

    def _cell(self, data: dict, article_id: int, warehouse_id: str) -> dict:
        stock = data.setdefault("stock", {})
        article = stock.setdefault(str(article_id), {})
        return article.setdefault(
            warehouse_id,
            {"qty": 0, "reserved": 0, "min_qty": 0},
        )

    def _next_id(self, data: dict) -> int:
        movements = data.get("movements") or []
        if not movements:
            return 1
        return max(int(item.get("id") or 0) for item in movements) + 1

    def _load(self) -> dict:
        if not self.path.exists():
            return self._default()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._default()
        if not isinstance(payload, dict):
            return self._default()
        warehouses = payload.get("warehouses")
        if not warehouses:
            payload["warehouses"] = self._default()["warehouses"]
        payload.setdefault("stock", {})
        payload.setdefault("movements", [])
        return payload

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _default() -> dict:
        return {
            "warehouses": [
                {"id": DEFAULT_WAREHOUSE_ID, "name": DEFAULT_WAREHOUSE_NAME},
            ],
            "stock": {},
            "movements": [],
        }


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


warehouse_service = WarehouseService()
