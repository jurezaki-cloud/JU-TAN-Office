"""Slovenian UPN QR payload (ZBS technical standard).

Checksum = sum(len(field) for fields 1..19) + 19, zero-padded to 3 digits.
QR is only built when IBAN and positive amount are present (never decorative).
"""

from __future__ import annotations

import re

from app.utils.money import money, to_decimal


def _clean(value: str, limit: int) -> str:
    text = re.sub(r"[\r\n]+", " ", str(value or "")).strip()
    return text[:limit]


def _iban(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def _amount_field(amount) -> str:
    cents = int(money(amount) * 100)
    if cents < 0:
        cents = 0
    return f"{cents:011d}"


def _due(value: str) -> str:
    raw = re.sub(r"\D", "", str(value or ""))
    if len(raw) == 8:
        # yyyymmdd → ddmmyyyy if looks like ISO
        if int(raw[:4]) > 1900:
            return raw[6:8] + raw[4:6] + raw[0:4]
        return raw
    return ""


def format_reference(invoice_number: str) -> str:
    digits = re.sub(r"\D", "", invoice_number or "") or "0"
    return f"SI00{digits}"


def build_upn_qr(
    *,
    iban: str,
    recipient_name: str,
    recipient_address: str = "",
    recipient_city: str = "",
    amount,
    reference: str,
    purpose: str = "Plačilo računa",
    purpose_code: str = "OTHR",
    due_date: str = "",
    payer_name: str = "",
    payer_address: str = "",
    payer_city: str = "",
) -> str | None:
    clean_iban = _iban(iban)
    if not clean_iban or len(clean_iban) < 15:
        return None
    if to_decimal(amount) <= 0:
        return None

    ref = _clean(reference.replace(" ", "") if reference else "", 26)
    if ref and not ref.upper().startswith(("SI", "RF")):
        ref = f"SI00{re.sub(r'\D', '', ref) or '0'}"

    fields = [
        "UPNQR",                          # 1
        "",                               # 2 payer IBAN
        "",                               # 3 deposit
        "",                               # 4 payer reference
        _clean(payer_name, 33),           # 5
        _clean(payer_address, 33),        # 6
        _clean(payer_city, 33),           # 7
        _amount_field(amount),            # 8
        "",                               # 9 payment date
        "",                               # 10 urgent
        _clean(purpose_code, 4) or "OTHR",  # 11
        _clean(purpose, 42),              # 12
        _due(due_date),                   # 13
        clean_iban,                       # 14
        ref[:26],                         # 15
        _clean(recipient_name, 33),       # 16
        _clean(recipient_address, 33),    # 17
        _clean(recipient_city, 33),       # 18
        "",                               # 19 reserve
    ]
    checksum = sum(len(field) for field in fields) + 19
    fields.append(f"{checksum:03d}")
    return "\n".join(fields) + "\n"
