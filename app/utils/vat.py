"""Company and document VAT regime helpers (Slovenian ZDDV-1 Art. 94)."""

from __future__ import annotations

from typing import Iterable

from app.utils.money import money, to_decimal

ARTICLE_94_NOTICE = (
    "DDV ni obračunan na podlagi 1. odstavka 94. člena ZDDV-1 "
    "(nisem zavezanec za DDV)."
)

VAT_LIABLE_YES = 1
VAT_LIABLE_NO = 0

WEBSITE_URL = "http://www.ju-tan.com"
WEBSITE_LABEL = "www.ju-tan.com"

DOCUMENT_FOOTER_MESSAGE = (
    "Hvala za vaše zaupanje. Trudimo se, da za vas vedno poiščemo najboljše rešitve."
)


def parse_vat_liable(value) -> bool:
    """True when the company/document is VAT-registered (zavezanec = DA)."""
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) != 0
    text = str(value).strip().upper()
    if text in {"0", "NE", "NO", "FALSE", "N"}:
        return False
    # Empty / unknown / DA → treat as VAT-liable (safe historical default).
    return True


def vat_liable_int(value) -> int:
    return VAT_LIABLE_YES if parse_vat_liable(value) else VAT_LIABLE_NO


def vat_liable_label(value) -> str:
    return "DA" if parse_vat_liable(value) else "NE"


def effective_vat_percent(vat_percent, *, vat_liable: bool = True):
    """Line VAT % used for calculations under the document regime."""
    if not vat_liable:
        return 0
    return to_decimal(vat_percent)


def assert_vat_consistent(
    *,
    vat_liable: bool,
    lines: Iterable | None,
    vat_total,
    show_article_94: bool = False,
) -> None:
    """
    Reject contradictory non-VAT documents (VAT amounts + Art. 94 notice).

    Historical VAT documents (vat_liable=True) are never forced through Art. 94.
    """
    if vat_liable:
        if show_article_94:
            raise ValueError(
                "Obvestilo po 94. členu ZDDV-1 ni dovoljeno na dokumentu zavezanega za DDV."
            )
        return

    if money(vat_total) != 0:
        raise ValueError(
            "Dokument nezavezanca za DDV ne sme vsebovati zneska DDV."
        )

    for line in lines or []:
        vat = _line_vat_percent(line)
        if money(vat) != 0:
            raise ValueError(
                "Postavke dokumenta nezavezanca za DDV ne smejo imeti DDV %."
            )


def _line_vat_percent(line) -> object:
    if isinstance(line, dict):
        return line.get("vat", 0)
    if len(line) >= 9:
        return line[6]
    if len(line) >= 8:
        return line[5]
    if len(line) >= 6:
        return line[3]
    return 0


def company_vat_liable() -> bool:
    """Current company VAT registration from the database (default DA)."""
    try:
        from app.database.company_repository import company_repository

        return company_repository.is_vat_liable()
    except Exception as exc:
        # Never invent NE on read failure — but do not hide the failure either.
        try:
            from app.core.logger import logger

            logger.warning("company_vat_liable fallback to DA: %s", exc)
        except Exception:
            pass
        return True
