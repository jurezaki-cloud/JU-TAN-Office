"""Regression tests for Offers module fixes (line total, PDF, conversion lock, refresh)."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import CONVERTED_OFFER_MESSAGE, offer_repository
from app.pdf.pdf_engine import PdfDocument, pdf_engine
from app.pdf.pdf_export import pdf_export
from app.services.offer_service import offer_service
from app.utils.money import as_float, document_totals, line_gross


TODAY = date.today().isoformat()


def _seed_customer_article(prefix="OFF"):
    customer_repository.add(
        f"{prefix} d.o.o.",
        f"{prefix}-Kontakt",
        "Ulica 1",
        "1000",
        "Ljubljana",
        "SI",
        "111",
        f"{prefix.lower()}@t.si",
        "",
    )
    customer = customer_repository.search(f"{prefix} d.o.o.")[0]
    article_repository.add(f"{prefix}-A", "Artikel", "", "kos", 150.0, 22)
    article = next(r for r in article_repository.get_all() if r[1] == f"{prefix}-A")
    return customer, article


def test_offer_line_total_qty6_price150_discount2_vat22():
    """ISSUE 1: displayed/persisted line gross must be 1076.04."""
    gross = line_gross(6, 150, 22, 2)
    assert gross == Decimal("1076.04")
    assert as_float(gross) == 1076.04

    row = ["A", "Artikel", 6, "kos", 150, 2, 22, 1098, 1]  # wrong stored total ignored
    totals = document_totals([row])
    assert totals["total"] == 1076.04


def test_invoice_item_dialog_get_data_includes_discount(qt_app):
    """Line Skupaj from item dialog must apply discount (shared invoice/offer editor)."""
    from app.database.company_repository import company_repository
    from app.utils.vat import vat_liable_int

    # Ensure VAT-registered regime for this calculation regression.
    row = company_repository.get_company()
    if row is not None:
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
            vat_liable_int(True),
        )

    customer_repository.add(
        "ITEMDLG d.o.o.", "X", "", "1000", "Ljubljana", "SI", "", "i@t.si", "",
    )
    article_repository.add("ITEM-DLG-1", "Storitev", "", "kos", 150.0, 22)
    from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog

    dialog = InvoiceItemDialog(vat_liable=True)
    # Select the seeded article if present
    for i in range(dialog.article.count()):
        data = dialog.article.itemData(i)
        if data and data[1] == "ITEM-DLG-1":
            dialog.article.setCurrentIndex(i)
            break
    dialog.quantity.setValue(6)
    dialog.price.setValue(150)
    dialog.discount.setValue(2)
    dialog.vat.setValue(22)
    dialog.calculate()
    assert "1076.04" in dialog.total.text().replace(" ", "")
    data = dialog.get_data()
    assert data[5] == 2.0  # discount percent
    assert data[7] == 1076.04  # line Skupaj
    dialog.close()


def test_offer_details_refresh_after_conversion(qt_app):
    """ISSUE 2: details panel must reload persisted status after convert."""
    customer, article = _seed_customer_article("REFR")
    offer_id = offer_repository.create(
        "PON-REFR-1", customer[0], TODAY, TODAY, "Osnutek", 150, 0, 33, 183, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 150, 0, 22, 183,
    )

    from app.modules.offers.offer_page import OfferPage

    page = OfferPage()
    page.refresh()
    # Select the offer in the model and load details as Osnutek
    row_index = next(i for i, row in enumerate(page.model.offers) if row[0] == offer_id)
    page.details.load_offer(page.model.offers[row_index])
    assert page.details.lblStatus.text() == "Osnutek"

    invoice_id, number = offer_service.convert_to_invoice(offer_id)
    assert invoice_id
    assert number

    page.refresh()
    page._reload_details(offer_id)
    assert page.details.lblStatus.text() == "Sprejeta"
    assert offer_repository.get_by_id(offer_id)[5] == "Sprejeta"
    page.close()


def test_offer_pdf_uses_validity_label_invoice_keeps_due_date(tmp_path, monkeypatch):
    """ISSUE 3: offer PDF says Velja do; invoice PDF keeps Rok plačila + Sklic."""
    from app.core import constants as const

    monkeypatch.setattr(const, "EXPORT_DIR", tmp_path)
    monkeypatch.setenv("JU_TAN_EXPORT_DIR", str(tmp_path))

    customer, article = _seed_customer_article("PDFSEM")
    offer_id = offer_repository.create(
        "PON-PDFSEM-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    invoice_id = invoice_repository.add(
        "RAC-PDFSEM-1", customer[0], TODAY, TODAY, 100, 0, 22, 122, "", "Izdan",
    )
    invoice_repository.add_item(
        invoice_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )

    offer_doc = PdfDocument(
        doc_type="offer",
        number="PON-PDFSEM-1",
        issue_date=TODAY,
        due_date=TODAY,
        reference="PON-PDFSEM-1",
        customer_name="X",
        items=[{"code": "C", "name": "N", "quantity": 1, "price": 100, "discount": 0, "vat": 22, "total": 122}],
        total=122,
    )
    invoice_doc = PdfDocument(
        doc_type="invoice",
        number="RAC-PDFSEM-1",
        issue_date=TODAY,
        due_date=TODAY,
        reference="SI00 RAC-PDFSEM-1",
        customer_name="X",
        items=[{"code": "C", "name": "N", "quantity": 1, "price": 100, "discount": 0, "vat": 22, "total": 122}],
        total=122,
    )

    def _labels(blocks):
        texts = []

        def walk(obj):
            if obj is None:
                return
            if hasattr(obj, "text") and isinstance(obj.text, str):
                texts.append(obj.text)
            if hasattr(obj, "content"):
                walk(getattr(obj, "content"))
            if hasattr(obj, "_cellvalues"):
                for row in obj._cellvalues:
                    for cell in row:
                        walk(cell)
            if isinstance(obj, (list, tuple)):
                for part in obj:
                    walk(part)

        walk(blocks)
        return " ".join(texts)

    offer_title = _labels(pdf_engine._title_block(offer_doc))
    invoice_title = _labels(pdf_engine._title_block(invoice_doc))
    assert "Velja do" in offer_title
    assert "Rok plačila" not in offer_title
    assert "Rok plačila" in invoice_title

    from app.pdf.pdf_company import load_company, load_pdf_options

    company = load_company()
    options = load_pdf_options()
    monkeypatch.setattr(pdf_engine, "_qr_flowable", lambda *a, **k: None)
    offer_pay = _labels(pdf_engine._payment_block(offer_doc, company, options))
    invoice_pay = _labels(pdf_engine._payment_block(invoice_doc, company, options))
    assert "Velja do" in offer_pay
    assert "Rok plačila" not in offer_pay
    assert "Sklic" not in offer_pay
    # Invoice due date lives in the title/meta block; payment shows Sklic + Namen.
    assert "Rok plačila" not in invoice_pay
    assert "Sklic" in invoice_pay
    assert "Namen" in invoice_pay

    # Full export still produces files (QR optional; do not require segno here)
    monkeypatch.setattr(pdf_engine, "_qr_flowable", lambda *a, **k: None)
    offer_path = pdf_export.export_offer(offer_id)
    invoice_path = pdf_export.export_invoice(invoice_id)
    assert Path(offer_path).exists()
    assert Path(invoice_path).exists()


def test_converted_offer_cannot_be_modified():
    """ISSUE 4: repository blocks updates after conversion."""
    customer, article = _seed_customer_article("LOCK")
    offer_id = offer_repository.create(
        "PON-LOCK-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    invoice_id, _number = offer_service.convert_to_invoice(offer_id)
    assert offer_service.is_converted(offer_id)
    assert offer_repository.get_converted_invoice_id(offer_id) == invoice_id

    try:
        offer_repository.update(
            offer_id, customer[0], TODAY, TODAY, "Osnutek", 50, 0, 11, 61, "hack",
        )
        assert False, "update must be rejected"
    except ValueError as exc:
        assert CONVERTED_OFFER_MESSAGE in str(exc)

    try:
        offer_repository.delete_items(offer_id)
        assert False, "delete_items must be rejected"
    except ValueError:
        pass

    # Generated invoice untouched
    inv = invoice_repository.get_by_id(invoice_id)
    assert float(inv[9]) == 122.0
    assert len(invoice_repository.get_items(invoice_id)) == 1


def test_converted_offer_cannot_create_second_invoice():
    """ISSUE 4: duplicate conversion must fail."""
    customer, article = _seed_customer_article("DUP")
    offer_id = offer_repository.create(
        "PON-DUP-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    first_id, first_number = offer_service.convert_to_invoice(offer_id)
    before = len(invoice_repository.get_all())
    try:
        offer_service.convert_to_invoice(offer_id)
        assert False, "second conversion must fail"
    except ValueError as exc:
        assert "že pretvorjena" in str(exc).lower() or "dovoljena" in str(exc).lower()
    after = len(invoice_repository.get_all())
    assert after == before
    assert invoice_repository.get_by_id(first_id)[1] == first_number


def test_sprejeta_without_conversion_remains_editable():
    """Manual Sprejeta without invoice link must still be editable."""
    customer, article = _seed_customer_article("MANUAL")
    offer_id = offer_repository.create(
        "PON-MANUAL-1", customer[0], TODAY, TODAY, "Sprejeta", 100, 0, 22, 122, "",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    assert not offer_service.is_converted(offer_id)
    offer_repository.update(
        offer_id, customer[0], TODAY, TODAY, "Sprejeta", 100, 0, 22, 122, "ok",
    )
    assert offer_repository.get_by_id(offer_id)[10] == "ok"


def test_existing_invoice_and_offer_money_math_still_pass():
    """ISSUE 6: existing calculation helpers remain correct."""
    assert line_gross(2, 100, 22, 10) == Decimal("219.60")
    assert line_gross(1, 100, 22, 0) == Decimal("122.00")
    rows = [
        ["A", "Item", 1, "kos", 100, 0, 22, 122, 1],
        ["B", "Item2", 2, "kos", 50, 0, 22, 122, 2],
    ]
    totals = document_totals(rows)
    assert totals["subtotal"] == 200.0
    assert totals["vat"] == 44.0
    assert totals["total"] == 244.0
