from __future__ import annotations

from datetime import date, datetime

from openpyxl.utils.datetime import from_excel

VAT_OK = {0, 5, 9.5, 22, 9.50}


def parse_number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace("€", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return False


def parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and value > 20000:
        try:
            return from_excel(value).date().isoformat()
        except Exception:
            return False
    text = str(value).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return False


def parse_vat(value):
    number = parse_number(value)
    if number is None:
        return 22.0, "warning"
    if number is False:
        return 22.0, "error"
    if number in VAT_OK or float(number) in VAT_OK:
        return float(number), "ok"
    if 0 <= float(number) <= 100:
        return float(number), "warning"
    return 22.0, "error"


class RowIssue:
    def __init__(self, row: int, level: str, message: str):
        self.row = row
        self.level = level
        self.message = message


def validate_rows(module: str, rows: list[dict], existing: set[str]) -> tuple[list[dict], list[RowIssue]]:
    issues: list[RowIssue] = []
    prepared: list[dict] = []
    seen = set()

    for index, raw in enumerate(rows, start=2):
        item = dict(raw)
        item["_row"] = index
        item["_skip"] = False
        item["_errors"] = []
        item["_warnings"] = []

        if module == "customers":
            name = str(item.get("company") or "").strip()
            if not name:
                _fail(item, issues, index, "error", "Prazno polje: Naziv stranke")
            key = name.casefold()
            if name and (key in seen or key in existing):
                _fail(item, issues, index, "skip", "Podvojena stranka")
            seen.add(key)
        elif module == "products":
            code = str(item.get("code") or "").strip()
            name = str(item.get("name") or "").strip()
            if not code:
                _fail(item, issues, index, "error", "Prazno polje: Šifra")
            if not name:
                _fail(item, issues, index, "error", "Prazno polje: Naziv")
            key = code.casefold()
            if code and (key in seen or key in existing):
                _fail(item, issues, index, "skip", "Podvojena šifra")
            seen.add(key)
            price = parse_number(item.get("price"))
            if price is False:
                _fail(item, issues, index, "error", "Napačna številka: Cena")
            else:
                item["price"] = 0.0 if price is None else price
            vat, vat_state = parse_vat(item.get("vat"))
            item["vat"] = vat
            if vat_state == "warning":
                _note(item, issues, index, "warning", "Neobičajen DDV, vrstica bo uvožena")
            elif vat_state == "error":
                _fail(item, issues, index, "error", "Napačen DDV")
        else:
            number = str(item.get("number") or "").strip()
            customer = str(item.get("customer") or "").strip()
            if not number:
                _fail(item, issues, index, "error", "Prazno polje: Številka")
            if not customer:
                _fail(item, issues, index, "error", "Prazno polje: Stranka")
            key = number.casefold()
            if number and (key in seen or key in existing):
                _fail(item, issues, index, "skip", "Podvojena številka dokumenta")
            seen.add(key)
            for field in ("issue_date", "due_date", "valid_until", "delivery_date"):
                if field not in item:
                    continue
                parsed = parse_date(item.get(field))
                if parsed is False:
                    _fail(item, issues, index, "error", f"Napačen datum: {field}")
                else:
                    item[field] = parsed or ""
            total = parse_number(item.get("total"))
            if total is False:
                _fail(item, issues, index, "error", "Napačna številka: Znesek")
            else:
                item["total"] = 0.0 if total is None else total

        prepared.append(item)
    return prepared, issues


def _fail(item, issues, row, level, message):
    if level == "skip":
        item["_skip"] = True
        item["_warnings"].append(message)
        issues.append(RowIssue(row, "skip", message))
        return
    item["_skip"] = True
    item["_errors"].append(message)
    issues.append(RowIssue(row, "error", message))


def _note(item, issues, row, level, message):
    item["_warnings"].append(message)
    issues.append(RowIssue(row, level, message))
