"""Validation and normalization used at the data boundary."""

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MONEY_QUANTUM = Decimal("0.01")
PERCENT_QUANTUM = Decimal("0.01")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def required_text(value, field_name, max_length=200):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Polje '{field_name}' je obvezno.")
    if len(text) > max_length:
        raise ValueError(
            f"Polje '{field_name}' je lahko dolgo največ {max_length} znakov."
        )
    return text


def optional_text(value, field_name, max_length=500):
    text = str(value or "").strip()
    if len(text) > max_length:
        raise ValueError(
            f"Polje '{field_name}' je lahko dolgo največ {max_length} znakov."
        )
    return text


def normalize_email(value):
    email = optional_text(value, "E-pošta", 254).lower()
    if email and not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("E-poštni naslov ni veljaven.")
    return email


def decimal_value(value, field_name, *, minimum=Decimal("0"), quantum=MONEY_QUANTUM):
    try:
        number = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"Polje '{field_name}' mora biti veljavno število.") from error
    if not number.is_finite() or number < minimum:
        raise ValueError(f"Polje '{field_name}' ne sme biti manjše od {minimum}.")
    return number


def money_for_storage(value, field_name="Znesek"):
    """Normalize money to two decimals before SQLite storage."""
    return float(decimal_value(value, field_name))


def percentage_for_storage(value, field_name="Odstotek"):
    number = decimal_value(value, field_name, quantum=PERCENT_QUANTUM)
    if number > Decimal("100"):
        raise ValueError(f"Polje '{field_name}' ne sme biti večje od 100.")
    return float(number)


def calculate_line_total(quantity, price, discount=0, vat=0):
    qty = decimal_value(quantity, "Količina", quantum=Decimal("0.001"))
    unit_price = decimal_value(price, "Cena")
    discount_rate = decimal_value(discount, "Popust", quantum=PERCENT_QUANTUM)
    vat_rate = decimal_value(vat, "DDV", quantum=PERCENT_QUANTUM)
    if discount_rate > 100 or vat_rate > 100:
        raise ValueError("Popust in DDV ne smeta biti večja od 100.")
    net = qty * unit_price * (Decimal("1") - discount_rate / Decimal("100"))
    gross = net * (Decimal("1") + vat_rate / Decimal("100"))
    return gross.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
