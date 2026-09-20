"""Validacija vhodov, varne poti in SQL zaščita."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ALLOWED_DOC_EXT = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".zip", ".txt"}
SYSTEM_NAMES = {"windows", "system32", "syswow64"}

SAFE_NAME = re.compile(r"^[\w .\-()čšžČŠŽ]+$", re.UNICODE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
TRR_RE = re.compile(r"^SI56\d{15}$")
VAT_RE = re.compile(r"^(SI)?\d{8}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def require_email(value: str, field: str = "e-pošta") -> str:
    text = require_non_empty(value, field)
    if not EMAIL_RE.match(text):
        raise ValueError(f"{field} ni veljaven e-naslov.")
    return text


def require_date(value: str, field: str = "datum") -> str:
    text = require_non_empty(value, field)
    if not DATE_RE.match(text):
        raise ValueError(f"{field} mora biti YYYY-MM-DD.")
    return text


def require_vat(value: str, field: str = "davčna") -> str:
    text = require_non_empty(value, field).upper().replace(" ", "")
    if not VAT_RE.match(text):
        raise ValueError(f"{field} ni veljavna (SI + 8 številk).")
    return text


def require_iban(value: str, field: str = "IBAN") -> str:
    text = require_non_empty(value, field).upper().replace(" ", "")
    if not IBAN_RE.match(text):
        raise ValueError(f"{field} ni veljaven.")
    return text


def require_trr(value: str, field: str = "TRR") -> str:
    text = require_non_empty(value, field).upper().replace(" ", "")
    if not TRR_RE.match(text):
        raise ValueError(f"{field} ni veljaven slovenski TRR (SI56…).")
    return text


def require_non_empty(value: str, field: str = "polje") -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} je obvezno.")
    return text


def require_number(value: Any, field: str = "število", minimum: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} mora biti število.") from exc
    if minimum is not None and number < minimum:
        raise ValueError(f"{field} mora biti vsaj {minimum}.")
    return number


def safe_filename(name: str) -> str:
    """Odstrani nevarne znake iz imena datoteke."""
    cleaned = re.sub(r"[^\w .\-()čšžČŠŽ]", "_", name or "dokument", flags=re.UNICODE)
    return cleaned.strip("._") or "dokument"


def ensure_inside(path: Path, root: Path) -> Path:
    """Prepreči path traversal izven korenske mape."""
    resolved = path.resolve()
    base = root.resolve()
    if base not in resolved.parents and resolved != base:
        raise PermissionError("Pot je izven dovoljene mape.")
    return resolved


ALLOWED_DOC_EXT = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".zip", ".txt"}
SYSTEM_NAMES = {"windows", "system32", "syswow64"}


def assert_safe_document(path: Path, root: Path) -> Path:
    resolved = ensure_inside(path, root)
    ext = resolved.suffix.lower()
    if ext and ext not in ALLOWED_DOC_EXT:
        raise ValueError("Nepodprta pripona datoteke.")
    parts = {part.lower() for part in resolved.parts}
    if parts & SYSTEM_NAMES:
        raise PermissionError("Prepovedan prepis sistemskih datotek.")
    return resolved


def parse_json_object(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Pričakovan je JSON objekt.")
    return data


def write_json_atomic(path: Path, data: dict) -> None:
    """Atomski zapis JSON (temp + replace), da se nastavitve ne pokvarijo."""
    if not isinstance(data, dict):
        raise ValueError("Nastavitve morajo biti objekt.")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def assert_parameterized(sql: str) -> None:
    """Zavrni očitno zlepljene SQL nize z vrednostmi."""
    if re.search(r"""['"]\s*\+|f['\"].*SELECT""", sql, re.IGNORECASE):
        raise ValueError("SQL mora uporabljati parametre.")
