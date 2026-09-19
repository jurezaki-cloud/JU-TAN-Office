"""VAT regime: company setting, document snapshot, Art. 94 notice, calculations."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.database.article_repository import article_repository
from app.database.company_repository import company_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.pdf.pdf_engine import PdfDocument, pdf_engine
from app.pdf.pdf_export import pdf_export
from app.utils.money import document_totals, line_gross
from app.utils.vat import (
    ARTICLE_94_NOTICE,
    DOCUMENT_FOOTER_MESSAGE,
    assert_vat_consistent,
    parse_vat_liable,
    vat_liable_int,
    vat_liable_label,
)


TODAY = date.today().isoformat()


def _seed(prefix: str):
    customer_repository.add(
        f"{prefix} d.o.o.",
        f"{prefix}-K",
        "Ulica 1",
        "1000",
        "Ljubljana",
        "SI",
        "111",
        f"{prefix.lower()}@t.si",
        "",
    )
    customer = customer_repository.search(f"{prefix} d.o.o.")[0]
    article_repository.add(f"{prefix}-A", "Storitev", "", "kos", 100.0, 22)
    article = next(r for r in article_repository.get_all() if r[1] == f"{prefix}-A")
    return customer, article


def _set_company_vat_liable(liable: bool) -> None:
    row = company_repository.get_company()
    assert row is not None
    company_repository.save(
        row[1] or "Test",
        row[2] or row[1] or "Test",
        row[3] or "",
        row[4] or "",
        row[5] or "",
        row[6] or "",
        row[7] or "",
        row[8] or "",
        row[9] or "",
        row[10] or "",
        row[11] or "",
        row[12] or "",
        row[13] or "",
        row[14] or "",
        row[15] or "",
        row[16] or "RAC",
        row[17] or "PON",
        int(row[18] or 1),
        int(row[19] or 1),
        float(row[20] if row[20] is not None else 22),
        row[21] or "",
        1 if liable else 0,
    )


def test_vat_liable_helpers():
    assert parse_vat_liable("DA") is True
    assert parse_vat_liable("NE") is False
    assert parse_vat_liable(0) is False
    assert parse_vat_liable(None) is True
    assert vat_liable_label(0) == "NE"
    assert vat_liable_int("NE") == 0


def test_company_vat_liable_persists():
    _set_company_vat_liable(False)
    assert company_repository.is_vat_liable() is False
    row = company_repository.get_company()
    assert vat_liable_label(row[22]) == "NE"

    _set_company_vat_liable(True)
    assert company_repository.is_vat_liable() is True


def test_vat_registered_company_calculation():
    rows = [["A", "Item", 1, "kos", 100, 0, 22, 122, 1]]
    totals = document_totals(rows, vat_liable=True)
    assert totals["vat"] == 22.0
    assert totals["total"] == 122.0
    assert line_gross(1, 100, 22, 0, vat_liable=True) == Decimal("122.00")


def test_non_vat_company_calculation_no_vat():
    rows = [["A", "Item", 1, "kos", 100, 0, 22, 122, 1]]
    totals = document_totals(rows, vat_liable=False)
    assert totals["vat"] == 0.0
    assert totals["total"] == 100.0
    assert line_gross(1, 100, 22, 10, vat_liable=False) == Decimal("90.00")


def test_article_94_notice_validation():
    assert_vat_consistent(
        vat_liable=False,
        lines=[["A", "Item", 1, "kos", 100, 0, 0, 100, 1]],
        vat_total=0,
        show_article_94=True,
    )
    with pytest.raises(ValueError):
        assert_vat_consistent(
            vat_liable=False,
            lines=[["A", "Item", 1, "kos", 100, 0, 22, 122, 1]],
            vat_total=22,
            show_article_94=True,
        )
    with pytest.raises(ValueError):
        assert_vat_consistent(
            vat_liable=True,
            lines=[],
            vat_total=0,
            show_article_94=True,
        )


def test_non_vat_invoice_and_offer_snapshot_and_pdf(tmp_path, monkeypatch):
    from app.core import constants as const

    monkeypatch.setattr(const, "EXPORT_DIR", tmp_path)
    monkeypatch.setenv("JU_TAN_EXPORT_DIR", str(tmp_path))
    monkeypatch.setattr(pdf_engine, "_qr_flowable", lambda *a, **k: None)

    _set_company_vat_liable(False)
    customer, article = _seed("NOVAT")

    offer_id = offer_repository.create(
        "PON-NOVAT-1",
        customer[0],
        TODAY,
        TODAY,
        "Osnutek",
        100,
        0,
        0,
        100,
        "",
        vat_liable=False,
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 0, 100,
    )
    assert offer_repository.get_vat_liable(offer_id) is False

    invoice_id = invoice_repository.add(
        "RAC-NOVAT-1",
        customer[0],
        TODAY,
        TODAY,
        100,
        0,
        0,
        100,
        "",
        "Izdan",
        vat_liable=False,
    )
    invoice_repository.add_item(
        invoice_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 0, 100,
    )
    assert invoice_repository.get_vat_liable(invoice_id) is False
    inv = invoice_repository.get_by_id(invoice_id)
    assert float(inv[8] or 0) == 0.0
    assert float(inv[9] or 0) == 100.0

    # Changing company setting must not rewrite historical documents.
    _set_company_vat_liable(True)
    assert invoice_repository.get_vat_liable(invoice_id) is False
    assert offer_repository.get_vat_liable(offer_id) is False

    offer_path = pdf_export.export_offer(offer_id)
    invoice_path = pdf_export.export_invoice(invoice_id)
    assert Path(offer_path).exists()
    assert Path(invoice_path).exists()
    assert Path(offer_path).stat().st_size > 500
    assert Path(invoice_path).stat().st_size > 500
    assert ARTICLE_94_NOTICE.startswith("DDV ni obračunan")

    # Restore company to VAT-registered so later tests are not polluted.
    _set_company_vat_liable(True)

def test_historical_vat_document_stable_when_company_changes():
    _set_company_vat_liable(True)
    customer, article = _seed("HIST")
    invoice_id = invoice_repository.add(
        "RAC-HIST-1",
        customer[0],
        TODAY,
        TODAY,
        100,
        0,
        22,
        122,
        "",
        "Izdan",
        vat_liable=True,
    )
    invoice_repository.add_item(
        invoice_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    _set_company_vat_liable(False)
    inv = invoice_repository.get_by_id(invoice_id)
    assert invoice_repository.get_vat_liable(invoice_id) is True
    assert float(inv[8]) == 22.0
    assert float(inv[9]) == 122.0
    _set_company_vat_liable(True)

def test_discounts_still_correct_under_both_regimes():
    rows = [["A", "Item", 6, "kos", 150, 2, 22, 1076.04, 1]]
    vat_on = document_totals(rows, vat_liable=True)
    assert vat_on["total"] == 1076.04
    vat_off = document_totals(rows, vat_liable=False)
    # 6×150=900, 2% → 882 net, no VAT
    assert vat_off["vat"] == 0.0
    assert vat_off["total"] == 882.0


def test_pdf_footer_message_and_article_94_in_engine(tmp_path):
    doc = PdfDocument(
        doc_type="invoice",
        number="RAC-FOOT-1",
        issue_date=TODAY,
        due_date=TODAY,
        customer_name="Kupec",
        items=[{"code": "C", "name": "N", "quantity": 1, "price": 50, "discount": 0, "vat": 0, "total": 50}],
        subtotal=50,
        vat=0,
        total=50,
        vat_liable=False,
    )
    path = pdf_engine.render(doc, tmp_path / "foot.pdf")
    assert path.exists()
    assert path.stat().st_size > 500
    assert ARTICLE_94_NOTICE
    assert "Hvala za vaše zaupanje" in DOCUMENT_FOOTER_MESSAGE
    # linkURL target is present in PDF annotations
    raw = path.read_bytes()
    assert b"www.ju-tan.com" in raw or b"ju-tan.com" in raw


def test_contradictory_non_vat_with_vat_amount_rejected():
    with pytest.raises(ValueError, match="ne sme vsebovati zneska DDV"):
        assert_vat_consistent(
            vat_liable=False,
            lines=[["A", "X", 1, "kos", 100, 0, 0, 100, 1]],
            vat_total=22,
            show_article_94=True,
        )


def test_settings_vat_liable_da_ne_roundtrip():
    """Persist DA → reload → NE → reload must match DB source of truth."""
    from app.modules.settings.settings_controller import SettingsController
    from app.utils.vat import company_vat_liable

    ctrl = SettingsController()
    bundle = ctrl.load_bundle()
    company = bundle["company"]
    assert company is not None
    base = {
        "name": company[1],
        "address": company[3] or "",
        "postal_code": company[4] or "",
        "city": company[5] or "",
        "country": company[6] or "",
        "phone": company[13] or "",
        "mobile": company[14] or "",
        "email": company[11] or "",
        "website": company[12] or "",
        "tax_number": company[7] or "",
        "registration_number": company[8] or "",
        "iban": company[9] or "",
        "swift": "",
        "logo": company[15] or "",
    }
    extras = bundle["extras"]

    base["vat_liable"] = "DA"
    ctrl.save_bundle(base, extras)
    assert company_repository.is_vat_liable() is True
    assert company_vat_liable() is True
    assert vat_liable_label(company_repository.get_company()[22]) == "DA"

    base["vat_liable"] = "NE"
    ctrl.save_bundle(base, extras)
    assert company_repository.is_vat_liable() is False
    assert company_vat_liable() is False
    assert vat_liable_label(company_repository.get_company()[22]) == "NE"

    # Restore DA for later tests in this module that expect VAT on by default.
    base["vat_liable"] = "DA"
    ctrl.save_bundle(base, extras)


def test_combo_ne_without_full_save_propagates_to_new_invoice(qt_app):
    """
    Regression for the manual GUI bug:

    Settings combo set to NE (even before clicking Shrani) must update the DB
    so a new InvoiceDialog does not charge VAT on article rate 22%.
    """
    from app.core.permissions import set_identity
    from app.modules.invoices.invoice_dialog import InvoiceDialog
    from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog
    from app.modules.invoices.invoice_page import InvoicePage
    from app.utils.money import as_float, document_totals, line_gross
    from app.utils.vat import ARTICLE_94_NOTICE, company_vat_liable
    from app.widgets.settings.company_card import CompanyCard

    set_identity(role="Administrator", authenticated=True)
    _set_company_vat_liable(True)
    assert company_vat_liable() is True

    card = CompanyCard()
    # Mimic user selecting NE without clicking the full Settings "Shrani".
    card.vat_liable.setCurrentText("NE")
    assert company_repository.is_vat_liable() is False
    assert company_vat_liable() is False

    page = InvoicePage()
    dialog = InvoiceDialog(page)
    assert dialog.vat_liable is False
    assert ARTICLE_94_NOTICE in dialog.lbl_vat_notice.text()
    assert dialog.items_table.isColumnHidden(6) is True

    item = InvoiceItemDialog(dialog, vat_liable=dialog.vat_liable)
    assert item.vat_liable is False
    assert item.vat.isEnabled() is False
    item.quantity.setValue(3)
    item.price.setValue(100)
    item.discount.setValue(2)
    # Article master still has 22% — must not be applied financially.
    item.vat.setValue(22)
    data = [
        "GUI-A",
        "Storitev",
        3.0,
        "kos",
        100.0,
        2.0,
        0 if not item.vat_liable else 22.0,
        as_float(line_gross(3, 100, 22, 2, vat_liable=item.vat_liable)),
        1,
    ]
    # Prefer real get_data when articles exist.
    if item.article.count():
        item.calculate()
        data = item.get_data()
        data[2] = 3.0
        data[4] = 100.0
        data[5] = 2.0
        data[6] = 0
        data[7] = as_float(line_gross(3, 100, 22, 2, vat_liable=False))

    dialog.items_model.add_item(data)
    dialog.update_total()
    totals = document_totals(dialog.items_model.items, vat_liable=dialog.vat_liable)
    assert totals["vat"] == 0.0
    assert totals["total"] == 294.0
    assert "294.00" in dialog.lbl_total.text().replace(" ", "")

    _set_company_vat_liable(True)


def test_invoice_dialog_vat_on_and_off_same_line(qt_app):
    """Same 3×100 @2% line: NE → 294.00, DA → 358.68."""
    from app.modules.invoices.invoice_dialog import InvoiceDialog
    from app.utils.money import as_float, document_totals, line_gross

    line_template = ["A", "X", 3.0, "kos", 100.0, 2.0, 22.0, 0.0, 1]

    _set_company_vat_liable(False)
    off = InvoiceDialog(None)
    assert off.vat_liable is False
    row_off = list(line_template)
    row_off[6] = 0
    row_off[7] = as_float(line_gross(3, 100, 22, 2, vat_liable=False))
    off.items_model.add_item(row_off)
    off.update_total()
    totals_off = document_totals(off.items_model.items, vat_liable=False)
    assert totals_off == {"subtotal": 300.0, "discount": 6.0, "vat": 0.0, "total": 294.0}

    _set_company_vat_liable(True)
    on = InvoiceDialog(None)
    assert on.vat_liable is True
    row_on = list(line_template)
    row_on[7] = as_float(line_gross(3, 100, 22, 2, vat_liable=True))
    on.items_model.add_item(row_on)
    on.update_total()
    totals_on = document_totals(on.items_model.items, vat_liable=True)
    assert totals_on["vat"] == 64.68
    assert totals_on["total"] == 358.68


def test_offer_and_order_dialogs_respect_company_ne(qt_app):
    from app.modules.offers.offer_dialog import OfferDialog
    from app.modules.orders.order_dialog import OrderDialog
    from app.utils.money import as_float, document_totals, line_gross

    _set_company_vat_liable(False)
    offer = OfferDialog(None)
    order = OrderDialog(None)
    assert offer.vat_liable is False
    assert order.vat_liable is False

    row = ["A", "X", 3.0, "kos", 100.0, 2.0, 0, as_float(line_gross(3, 100, 22, 2, vat_liable=False)), 1]
    offer.items_model.add_item(row)
    order.items_model.add_item(row)
    offer.update_total()
    order.update_total()
    assert document_totals(offer.items_model.items, vat_liable=False)["total"] == 294.0
    assert document_totals(order.items_model.items, vat_liable=False)["total"] == 294.0
    assert offer.items_table.isColumnHidden(6) is True
    assert order.items_table.isColumnHidden(6) is True

    _set_company_vat_liable(True)


def test_parse_vat_liable_rejects_bool_string_trap():
    """bool('NE') is True — parse_vat_liable must remain the only converter."""
    assert bool("NE") is True
    assert parse_vat_liable("NE") is False
    assert parse_vat_liable("0") is False
    assert vat_liable_int("NE") == 0
