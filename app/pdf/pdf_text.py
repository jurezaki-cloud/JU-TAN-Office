"""Text formatting for PDF documents (Slovenian notation, safe Paragraph markup)."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from xml.sax.saxutils import escape

from app.utils.money import to_decimal

NBSP = "\u00a0"


def esc(value) -> str:
    """User text for a ReportLab Paragraph, where &, < and > are markup."""
    return escape("" if value is None else str(value))


def format_iban(value, sep: str = NBSP) -> str:
    """Print form in groups of four; with the default NBSP the groups never wrap apart."""
    compact = re.sub(r"\s+", "", str(value or "")).upper()
    if not compact:
        return ""
    return sep.join(compact[i : i + 4] for i in range(0, len(compact), 4))


def format_quantity(value) -> str:
    """2 → "2", 2.5 → "2,5", 0.125 → "0,125" (REAL columns must not show "2.0")."""
    amount = to_decimal(value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if amount == amount.to_integral_value():
        return str(int(amount))
    return f"{amount.normalize():f}".replace(".", ",")


def format_percent(value) -> str:
    """22 → "22 %", 9.5 → "9,5 %"."""
    amount = to_decimal(value)
    if amount == amount.to_integral_value():
        return f"{int(amount)} %"
    return f"{amount.normalize():f}".replace(".", ",") + " %"


__all__ = ["NBSP", "esc", "format_iban", "format_percent", "format_quantity"]
