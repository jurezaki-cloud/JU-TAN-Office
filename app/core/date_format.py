from __future__ import annotations

from datetime import date, datetime

DISPLAY_DATE_FORMAT = "dd-MM-yyyy"
DISPLAY_DATE_PY_FORMAT = "%d-%m-%Y"


def format_date(value, fallback: str = "—") -> str:
    # Format an ISO/database date for people without changing stored values.
    if value is None or value == "":
        return fallback
    if isinstance(value, datetime):
        return value.strftime(DISPLAY_DATE_PY_FORMAT)
    if isinstance(value, date):
        return value.strftime(DISPLAY_DATE_PY_FORMAT)
    text = str(value).strip()
    if not text:
        return fallback
    try:
        return date.fromisoformat(text[:10]).strftime(DISPLAY_DATE_PY_FORMAT)
    except ValueError:
        return text
