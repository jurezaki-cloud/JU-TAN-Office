"""Exact monetary calculations for offers."""

from decimal import Decimal, ROUND_HALF_UP

from app.core.validation import decimal_value

CENT = Decimal("0.01")


def calculate_item(item):
    quantity = decimal_value(
        item.get("quantity", 0), "Količina", quantum=Decimal("0.001")
    )
    price = decimal_value(item.get("price", 0), "Cena")
    discount_rate = decimal_value(item.get("discount", 0), "Popust")
    vat_rate = decimal_value(item.get("vat", 0), "DDV")
    if discount_rate > 100 or vat_rate > 100:
        raise ValueError("Popust in DDV ne smeta biti večja od 100.")

    base = (quantity * price).quantize(CENT, rounding=ROUND_HALF_UP)
    discount = (base * discount_rate / 100).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    net = base - discount
    vat = (net * vat_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    total = net + vat
    return {
        "base": base,
        "discount_amount": discount,
        "net": net,
        "vat_amount": vat,
        "total": total,
    }


def calculate_offer(items):
    result = {
        "subtotal": Decimal("0.00"),
        "discount": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "total": Decimal("0.00"),
    }
    calculated_items = []
    for item in items:
        amounts = calculate_item(item)
        normalized = dict(item)
        normalized["total"] = amounts["total"]
        calculated_items.append(normalized)
        result["subtotal"] += amounts["base"]
        result["discount"] += amounts["discount_amount"]
        result["vat"] += amounts["vat_amount"]
        result["total"] += amounts["total"]
    result["items"] = calculated_items
    return result
