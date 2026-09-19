"""Centralized money math for JU-TAN Office (EUR, 2-decimal round-half-up)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Iterable

TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")


def to_decimal(value) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def money(value) -> Decimal:
    """Round to 2 decimal places (banker's half-up for EUR display)."""
    return to_decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def as_float(value) -> float:
    """Persist as float for existing SQLite REAL columns."""
    return float(money(value))


def format_eur(value, *, spaced: bool = True) -> str:
    amount = money(value)
    text = f"{amount:,.2f}"
    if spaced:
        text = text.replace(",", " ")
    else:
        text = text.replace(",", "")
    return f"{text} €"


def line_net(quantity, unit_price, discount_percent=0) -> Decimal:
    """Net amount for one line after percentage discount, before VAT."""
    base = to_decimal(quantity) * to_decimal(unit_price)
    discount = base * to_decimal(discount_percent) / HUNDRED
    return money(base - discount)


def line_discount_amount(quantity, unit_price, discount_percent=0) -> Decimal:
    base = to_decimal(quantity) * to_decimal(unit_price)
    return money(base * to_decimal(discount_percent) / HUNDRED)


def line_vat(quantity, unit_price, vat_percent, discount_percent=0) -> Decimal:
    net = line_net(quantity, unit_price, discount_percent)
    return money(net * to_decimal(vat_percent) / HUNDRED)


def line_gross(quantity, unit_price, vat_percent, discount_percent=0) -> Decimal:
    net = line_net(quantity, unit_price, discount_percent)
    return money(net + line_vat(quantity, unit_price, vat_percent, discount_percent))


def document_totals(lines: Iterable) -> dict[str, float]:
    """
    Aggregate document totals from line tuples/lists.

    Each line must expose quantity, price, discount%, vat% at indexes
    compatible with editor rows: [..., qty, unit, price, discount?, vat]
    or dicts with keys quantity/price/discount/vat.
    """
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    vat_total = Decimal("0")
    gross_total = Decimal("0")

    for line in lines:
        qty, price, discount, vat = _unpack_line(line)
        base = to_decimal(qty) * to_decimal(price)
        disc = base * to_decimal(discount) / HUNDRED
        net = base - disc
        vat_amt = net * to_decimal(vat) / HUNDRED
        subtotal += money(base)
        discount_total += money(disc)
        vat_total += money(vat_amt)
        gross_total += money(net + vat_amt)

    return {
        "subtotal": as_float(subtotal),
        "discount": as_float(discount_total),
        "vat": as_float(vat_total),
        "total": as_float(gross_total),
    }


def _unpack_line(line) -> tuple:
    if isinstance(line, dict):
        return (
            line.get("quantity", 0),
            line.get("price", 0),
            line.get("discount", 0),
            line.get("vat", 0),
        )
    # Editor item row: [code, name, qty, unit, price, vat, total, article_id]
    # or with discount: [code, name, qty, unit, price, discount, vat, total, article_id]
    if len(line) >= 9:
        return line[2], line[4], line[5], line[6]
    if len(line) >= 8:
        # legacy without discount column in UI row
        return line[2], line[4], 0, line[5]
    if len(line) >= 6:
        return line[0], line[1], line[2], line[3]
    raise ValueError("Unrecognized line format for money totals")
