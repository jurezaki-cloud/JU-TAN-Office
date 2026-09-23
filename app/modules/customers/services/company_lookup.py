"""Company lookup integration for the customer form.

The desktop app talks only to JU-TAN's HTTPS backend. Provider credentials
(AJPES or another approved registry source) must stay server-side and must
never be shipped in the Windows application.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_LOOKUP_URL = "https://www.ju-tan.com/api/v1/company-lookup"


class CompanyLookupError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompanyLookupResult:
    company: str
    address: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = "Slovenija"
    tax_number: str = ""


def normalize_tax_number(value: str) -> str:
    value = re.sub(r"\s+", "", (value or "").upper())
    if value.startswith("SI"):
        value = value[2:]
    if not re.fullmatch(r"\d{8}", value):
        raise CompanyLookupError("Vnesite veljavno 8-mestno slovensko davčno številko.")
    return value


def lookup_company(tax_number: str, *, timeout: float = 8.0) -> CompanyLookupResult:
    tax_number = normalize_tax_number(tax_number)
    base_url = os.getenv("JU_TAN_COMPANY_LOOKUP_URL", DEFAULT_LOOKUP_URL).rstrip("/")
    request = Request(
        f"{base_url}?tax_number={tax_number}",
        headers={"Accept": "application/json", "User-Agent": "JU-TAN-Office"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            raise CompanyLookupError("Podjetja s to davčno številko ni bilo mogoče najti.") from exc
        raise CompanyLookupError("Iskanje podjetja trenutno ni na voljo.") from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise CompanyLookupError("Povezava s storitvijo za iskanje podjetij ni uspela.") from exc

    data = payload.get("company") if isinstance(payload, dict) else None
    if not isinstance(data, dict) or not str(data.get("company") or "").strip():
        raise CompanyLookupError("Podjetja s to davčno številko ni bilo mogoče najti.")

    return CompanyLookupResult(
        company=str(data.get("company") or "").strip(),
        address=str(data.get("address") or "").strip(),
        postal_code=str(data.get("postal_code") or "").strip(),
        city=str(data.get("city") or "").strip(),
        country=str(data.get("country") or "Slovenija").strip() or "Slovenija",
        tax_number=tax_number,
    )
