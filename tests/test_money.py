"""Unit tests for centralized EUR money helpers."""

from decimal import Decimal

from app.utils.money import (
    as_float,
    document_totals,
    format_eur,
    line_gross,
    line_net,
    line_vat,
    money,
)


def test_money_rounds_half_up():
    assert money("1.005") == Decimal("1.01")
    assert money("1.004") == Decimal("1.00")


def test_line_with_vat_and_discount():
    # 2 × 100 = 200, 10% discount → 180 net, 22% VAT → 39.60, gross 219.60
    assert line_net(2, 100, 10) == Decimal("180.00")
    assert line_vat(2, 100, 22, 10) == Decimal("39.60")
    assert line_gross(2, 100, 22, 10) == Decimal("219.60")


def test_offer_line_total_regression_6x150_discount2_vat22():
    # 6 × 150 = 900, 2% → 882 net, 22% VAT → 194.04, gross 1076.04
    assert line_gross(6, 150, 22, 2) == Decimal("1076.04")


def test_document_totals_multi_line():
    rows = [
        ["A", "Item", 1, "kos", 100, 22, 122, 1],
        ["B", "Item2", 2, "kos", 50, 9.5, 109.5, 2],
    ]
    totals = document_totals(rows)
    assert totals["subtotal"] == 200.0  # 100 + 100
    assert totals["discount"] == 0.0
    assert totals["vat"] == 31.5  # 22 + 9.5
    assert totals["total"] == 231.5


def test_format_eur_spaced():
    assert format_eur(1234.5) == "1 234.50 €"
    assert as_float(line_gross(1, 10, 22)) == 12.2


def test_non_vat_document_totals_ignore_line_vat_percent():
    rows = [["A", "Item", 2, "kos", 100, 10, 22, 0, 1]]
    totals = document_totals(rows, vat_liable=False)
    # 2×100=200, 10% → 180 net, VAT forced off
    assert totals["discount"] == 20.0
    assert totals["vat"] == 0.0
    assert totals["total"] == 180.0
