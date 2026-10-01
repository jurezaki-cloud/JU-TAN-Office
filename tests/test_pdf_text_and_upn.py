"""PDF text formatting, VAT recap rows, signer resolution and UPN sanitising."""

from __future__ import annotations

from app.pdf.pdf_branding import extract_signer_name, resolve_signer_name
from app.pdf.pdf_tables import _vat_rows
from app.pdf.pdf_text import NBSP, esc, format_iban, format_percent, format_quantity
from app.pdf.upn_qr import build_upn_qr
from app.utils.money import document_totals, money, vat_breakdown

IBAN = "SI56 0237 9205 8132 832"


def _line(qty, price, vat, discount=0):
    return {"quantity": qty, "price": price, "discount": discount, "vat": vat}


def test_escape_keeps_zero_and_markup_literal():
    assert esc(None) == ""
    assert esc(0) == "0"
    assert esc("A & B <C>") == "A &amp; B &lt;C&gt;"


def test_quantity_and_percent_use_slovenian_notation():
    assert format_quantity(2) == "2"
    assert format_quantity(2.0) == "2"
    assert format_quantity(2.5) == "2,5"
    assert format_quantity(0.125) == "0,125"
    assert format_quantity(1.0005) == "1,001"
    assert format_percent(22) == "22 %"
    assert format_percent(9.5) == "9,5 %"
    assert format_percent(0) == "0 %"


def test_iban_prints_in_groups_of_four():
    assert format_iban("si56023792058132832") == NBSP.join(["SI56", "0237", "9205", "8132", "832"])
    assert format_iban(IBAN, sep=" ") == IBAN
    assert format_iban("") == ""


def test_vat_breakdown_adds_up_to_document_totals():
    lines = [_line(3, 19.99, 22, 5), _line(1, 7.35, 9.5), _line(2.5, 4.1, 9.5, 10), _line(1, 100, 5)]
    totals = document_totals(lines)
    groups = vat_breakdown(lines)
    assert [g["rate"] for g in groups] == [22.0, 9.5, 5.0]
    assert money(sum(g["base"] for g in groups)) == money(totals["subtotal"]) - money(totals["discount"])
    assert money(sum(g["vat"] for g in groups)) == money(totals["vat"])
    assert vat_breakdown(lines, vat_liable=False)[0]["vat"] == 0


def test_mixed_rates_list_base_and_vat_per_rate():
    lines = [_line(1, 100, 22), _line(1, 50, 9.5)]
    totals = document_totals(lines)
    rows = dict(_vat_rows(totals["subtotal"], totals["discount"], totals["vat"], lines))
    assert rows == {
        "Osnova za DDV 22 %:": 100.0,
        "DDV (22 %):": 22.0,
        "Osnova za DDV 9,5 %:": 50.0,
        "DDV (9,5 %):": 4.75,
    }


def test_discounted_single_rate_shows_taxable_base():
    lines = [_line(2, 100, 22, 10)]
    totals = document_totals(lines)
    rows = _vat_rows(totals["subtotal"], totals["discount"], totals["vat"], lines)
    assert rows[0] == ("Osnova za DDV:", money(180))
    assert rows[1] == ("DDV (22 %):", totals["vat"])


def test_stored_vat_that_disagrees_with_lines_is_not_split_per_rate():
    lines = [_line(1, 100, 22), _line(1, 50, 9.5)]
    rows = _vat_rows(150, 0, 30.0, lines)
    assert rows == [("DDV:", 30.0)]


def test_signer_resolution():
    assert extract_signer_name("Janez Novak s.p.") == "Janez Novak"
    assert extract_signer_name("Mizarstvo Novak d.o.o.") == ""
    assert extract_signer_name("Novak, d.o.o.") == ""
    assert extract_signer_name("Gradnje Kovač d.n.o.") == ""
    assert resolve_signer_name("JU-TAN studio", "Tanja Hrup") == "Tanja Hrup"
    assert resolve_signer_name("JU-TAN studio, Tanja Hrup s.p.", "  ") == "Tanja Hrup"
    assert resolve_signer_name("Acme d.o.o.") == ""


def _fields(payload: str) -> list[str]:
    assert payload.endswith("\n")
    return payload[:-1].split("\n")


def test_upn_payload_replaces_typographic_characters_and_stays_valid():
    payload = build_upn_qr(
        iban=IBAN,
        recipient_name="Studio „Lepota“ – Šenčur",
        recipient_address="Cesta <5> 12",
        recipient_city="4208 Šenčur",
        amount=246.07,
        reference="SI00 0007",
        purpose="Plačilo – račun „A“ 5 €…",
        payer_name="„Mizarstvo & Co“ d.o.o.",
    )
    assert payload is not None
    payload.encode("iso-8859-2")
    fields = _fields(payload)
    assert len(fields) == 20
    assert int(fields[19]) == sum(len(f) for f in fields[:19]) + 19
    assert fields[8] == "00000024607"
    assert fields[15] == "SI000007"
    assert fields[16] == 'Studio "Lepota" - Šenčur'
    assert fields[12] == 'Plačilo - račun "A" 5 EUR...'
    assert fields[5] == '"Mizarstvo & Co" d.o.o.'


def test_upn_payload_strips_line_breaks_that_would_shift_fields():
    payload = build_upn_qr(
        iban=IBAN,
        recipient_name="JU-TAN\nstudio",
        amount=10,
        reference="SI00 1",
        purpose="Vrstica 1\r\nVrstica 2",
    )
    fields = _fields(payload)
    assert len(fields) == 20
    assert fields[16] == "JU-TAN studio"
    assert fields[12] == "Vrstica 1 Vrstica 2"
