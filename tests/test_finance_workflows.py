"""Tests for offer→invoice conversion and payment ledger."""

from datetime import date, timedelta

from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.payment_repository import payment_repository
from app.pdf.upn_qr import build_upn_qr, format_reference


TODAY = date.today().isoformat()


def test_offer_items_convert_math_compatible(tmp_path, monkeypatch):
    # ensure repos talk to test DB via conftest
    customer_repository.add(
        "CONV d.o.o.", "Ana", "Ulica 1", "1000", "Ljubljana", "SI", "12345678", "a@t.si", "040",
    )
    customer = customer_repository.search("CONV d.o.o.")[0]
    article_repository.add("CONV-1", "Storitev", "", "ura", 100.0, 22)
    article = next(r for r in article_repository.get_all() if r[1] == "CONV-1")
    offer_id = offer_repository.create(
        "PON-CONV-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "ura", 100, 0, 22, 122,
    )
    offer = offer_repository.get_by_id(offer_id)
    items = offer_repository.get_items(offer_id)
    assert offer is not None
    assert len(items) == 1

    number = invoice_repository.get_next_number()
    invoice_id = invoice_repository.add(
        number, offer[2], TODAY, TODAY, offer[6], offer[7], offer[8], offer[9], "", "Izdan",
    )
    for item in items:
        invoice_repository.add_item(
            invoice_id, item[1], item[2], item[3], item[4] or "", item[5], item[6],
            item[7], item[8] or 0, item[9], item[10],
        )
    inv = invoice_repository.get_by_id(invoice_id)
    assert float(inv[9]) == 122.0
    assert len(invoice_repository.get_items(invoice_id)) == 1


def test_partial_and_full_payment():
    customer_repository.add(
        "PAY d.o.o.", "Bojan", "", "2000", "Maribor", "SI", "", "p@t.si", "",
    )
    customer = customer_repository.search("PAY d.o.o.")[0]
    invoice_id = invoice_repository.add(
        "RAC-PAY-1", customer[0], TODAY, TODAY, 100, 0, 22, 122, "", "Izdan",
    )
    payment_repository.ensure_schema()
    payment_repository.add(invoice_id, TODAY, 50, "Nakazilo")
    status = payment_repository.sync_invoice_status(invoice_id, 122)
    assert status == "Delno plačan"
    assert payment_repository.remaining(invoice_id, 122) == 72.0

    payment_repository.add(invoice_id, TODAY, 72, "Nakazilo")
    status = payment_repository.sync_invoice_status(invoice_id, 122)
    assert status == "Plačan"
    assert payment_repository.remaining(invoice_id, 122) == 0.0


def test_upn_qr_requires_iban_and_amount():
    assert build_upn_qr(
        iban="",
        recipient_name="Test",
        amount=10,
        reference="SI00 1",
    ) is None
    payload = build_upn_qr(
        iban="SI56031001001018518",
        recipient_name="JU-TAN d.o.o.",
        recipient_address="Ulica 1",
        recipient_city="1000 Ljubljana",
        amount=122.50,
        reference=format_reference("RAC-2026-001"),
        due_date=(date.today() + timedelta(days=14)).isoformat(),
    )
    assert payload is not None
    assert payload.startswith("UPNQR\n")
    assert "SI56031001001018518" in payload
