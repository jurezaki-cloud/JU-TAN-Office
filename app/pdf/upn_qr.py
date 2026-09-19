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


def _valid_iban(value: str) -> bool:
    iban = _iban(value)
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
    return int(numeric) % 97 == 1


def _valid_reference(value: str) -> bool:
    ref = re.sub(r"\s+", "", str(value or "")).upper()
    if not ref:
        return False
    if ref.startswith("RF"):
        if not re.fullmatch(r"RF[0-9]{2}[A-Z0-9]{1,21}", ref):
            return False
        rearranged = ref[4:] + ref[:4]
        numeric = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
        return int(numeric) % 97 == 1
    if ref.startswith("SI"):
        return bool(re.fullmatch(r"SI[0-9]{2}[0-9\-]{1,22}", ref))
    return False


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
            return f"{raw[6:8]}.{raw[4:6]}.{raw[0:4]}"
        return f"{raw[0:2]}.{raw[2:4]}.{raw[4:8]}"
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
    if not _valid_iban(clean_iban):
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
        "",                               # 4 withdrawal
        "",                               # 5 payer reference
        _clean(payer_name, 33),           # 6
        _clean(payer_address, 33),        # 7
        _clean(payer_city, 33),           # 8
        _amount_field(amount),            # 9
        "",                               # 10 payment date
        "",                               # 11 urgent
        _clean(purpose_code, 4) or "OTHR",  # 12
        _clean(purpose, 42),              # 13
        _due(due_date),                   # 14
        clean_iban,                       # 15
        ref[:26],                         # 16
        _clean(recipient_name, 33),       # 17
        _clean(recipient_address, 33),    # 18
        _clean(recipient_city, 33),       # 19
    ]
    if not _valid_reference(ref):
        return None

    checksum = sum(len(field) for field in fields) + 19
    fields.append(f"{checksum:03d}")
    return "\n".join(fields) + "\n"
