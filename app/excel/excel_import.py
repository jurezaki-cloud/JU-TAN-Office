from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.excel.excel_export import analyze_file, map_rows, write_workbook
from app.excel.excel_mapping import MODULES, suggest_mapping
from app.excel.excel_validation import validate_rows


@dataclass
class ImportSummary:
    imported: int = 0
    skipped: int = 0
    warnings: int = 0
    errors: int = 0
    messages: list[str] = field(default_factory=list)


def existing_keys(module: str) -> set[str]:
    if module == "customers":
        return {str(row[1]).casefold() for row in customer_repository.get_all() if row[1]}
    if module == "products":
        return {str(row[1]).casefold() for row in article_repository.get_all() if row[1]}
    if module == "invoices":
        return {str(row[1]).casefold() for row in invoice_repository.get_all() if row[1]}
    if module == "offers":
        return {str(row[1]).casefold() for row in offer_repository.get_all() if row[1]}
    if module == "orders":
        return {str(row[1]).casefold() for row in order_repository.get_all() if row[1]}
    return set()


def customer_id_by_name(name: str):
    target = (name or "").strip().casefold()
    for row in customer_repository.get_all():
        if str(row[1] or "").strip().casefold() == target:
            return row[0]
    return None


def export_module(module: str, path) -> None:
    headers = [field.label for field in MODULES[module]["fields"]]
    rows = []
    if module == "customers":
        for row in customer_repository.get_all():
            full = customer_repository.get_by_id(row[0])
            if not full:
                continue
            rows.append([
                full[1], full[2], full[3], full[4], full[5],
                full[6], full[7], full[8], full[9],
            ])
    elif module == "products":
        for row in article_repository.get_all():
            detail = article_repository.get_by_id(row[0])
            rows.append([
                row[1], row[2],
                detail[3] if detail else "",
                row[3], row[4], row[5],
            ])
    elif module == "invoices":
        for row in invoice_repository.get_all():
            full = invoice_repository.get_by_id(row[0])
            rows.append([
                row[1], row[3], row[2],
                full[4] if full else "",
                row[4], row[5],
                full[10] if full else "",
            ])
    elif module == "offers":
        for row in offer_repository.get_all():
            full = offer_repository.get_by_id(row[0])
            rows.append([
                row[1], row[2], row[3], row[4], row[6], row[5],
                full[10] if full else "",
            ])
    elif module == "orders":
        for row in order_repository.get_all():
            full = order_repository.get_by_id(row[0])
            rows.append([
                row[1], row[2], row[3], row[4], row[6], row[5],
                full[10] if full else "",
            ])
    write_workbook(path, module, headers, rows)


def export_template(module: str, path) -> None:
    headers = [field.label for field in MODULES[module]["fields"]]
    sample = {
        "customers": ["Primer d.o.o.", "Kontakt", "Naslov 1", "1000", "Ljubljana", "SI", "", "info@primer.si", ""],
        "products": ["ART-001", "Artikel", "", "kos", 10, 22],
        "invoices": ["RAC-0001", "Primer d.o.o.", date.today().isoformat(), "", 122, "Osnutek", ""],
        "offers": ["PON-0001", "Primer d.o.o.", date.today().isoformat(), "", 122, "Osnutek", ""],
        "orders": ["NAR-0001", "Primer d.o.o.", date.today().isoformat(), "", 122, "Osnutek", ""],
    }
    write_workbook(path, module, headers, [sample[module]], template=True)


def run_import(module: str, path, mapping: dict[str, str]) -> ImportSummary:
    from app.core.permissions import audit, require

    require("write")
    audit("create", f"import:{module}")
    analysis = analyze_file(path)
    mapped = map_rows(analysis, mapping)
    prepared, issues = validate_rows(module, mapped, existing_keys(module))
    summary = ImportSummary(
        warnings=len([i for i in issues if i.level == "warning"]),
        errors=len([i for i in issues if i.level == "error"]),
        messages=[f"Vrstica {i.row}: {i.message}" for i in issues[:50]],
    )
    for item in prepared:
        if item.get("_skip"):
            summary.skipped += 1
            continue
        try:
            _insert(module, item)
            summary.imported += 1
        except Exception as exc:
            summary.errors += 1
            summary.skipped += 1
            summary.messages.append(f"Vrstica {item.get('_row')}: {exc}")
    return summary


def _split_gross(total: float, vat_rate: float) -> tuple[float, float, float]:
    """Split imported gross into subtotal + VAT using a rate (e.g. 22)."""
    from app.utils.money import as_float, money, to_decimal

    gross = to_decimal(total)
    rate = to_decimal(vat_rate)
    if rate <= 0:
        return as_float(gross), 0.0, as_float(gross)
    net = money(gross / (1 + rate / 100))
    vat = money(gross - net)
    return as_float(net), as_float(vat), as_float(gross)


def _insert(module: str, item: dict) -> None:
    if module == "customers":
        customer_repository.add(
            item.get("company") or "",
            item.get("contact") or "",
            item.get("address") or "",
            item.get("postal_code") or "",
            item.get("city") or "",
            item.get("country") or "",
            item.get("tax_number") or "",
            item.get("email") or "",
            item.get("phone") or "",
        )
        return
    if module == "products":
        article_repository.add(
            str(item.get("code") or "").strip(),
            str(item.get("name") or "").strip(),
            str(item.get("description") or ""),
            str(item.get("unit") or "kos"),
            float(item.get("price") or 0),
            float(item.get("vat") or 22),
        )
        return
    customer_id = customer_id_by_name(str(item.get("customer") or ""))
    if customer_id is None:
        raise ValueError("Stranka ni v registru")
    total = float(item.get("total") or 0)
    # Header imports typically provide gross only; reverse-split at 22% unless vat_rate given.
    vat_rate = float(item.get("vat_rate") or 22)
    if item.get("subtotal") not in (None, "") and item.get("vat_amount") not in (None, ""):
        subtotal = float(item.get("subtotal") or 0)
        vat_amount = float(item.get("vat_amount") or 0)
        total = float(item.get("total") or (subtotal + vat_amount))
    else:
        subtotal, vat_amount, total = _split_gross(total, vat_rate)
    today = date.today().isoformat()
    if module == "invoices":
        invoice_repository.add(
            str(item.get("number")).strip(),
            customer_id,
            item.get("issue_date") or today,
            item.get("due_date") or item.get("issue_date") or today,
            subtotal,
            float(item.get("discount") or 0),
            vat_amount,
            total,
            str(item.get("notes") or ""),
            status=str(item.get("status") or "Osnutek"),
        )
        return
    if module == "offers":
        offer_repository.create(
            str(item.get("number")).strip(),
            customer_id,
            item.get("issue_date") or today,
            item.get("valid_until") or "",
            str(item.get("status") or "Osnutek"),
            subtotal,
            float(item.get("discount") or 0),
            vat_amount,
            total,
            str(item.get("notes") or ""),
        )
        return
    order_repository.create(
        number=str(item.get("number")).strip(),
        customer_id=customer_id,
        issue_date=item.get("issue_date") or today,
        delivery_date=item.get("delivery_date") or "",
        status=str(item.get("status") or "Osnutek"),
        subtotal=subtotal,
        discount=float(item.get("discount") or 0),
        vat=vat_amount,
        total=total,
        notes=str(item.get("notes") or ""),
    )
