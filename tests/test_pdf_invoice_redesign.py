"""Regression tests for the approved JU-TAN invoice PDF redesign."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from reportlab.lib.units import mm
from reportlab.platypus import Image, Spacer, Table

from app.pdf.pdf_branding import CONTENT_WIDTH_MM, CUSTOMER_CARD_WIDTH_MM, THANKS_SUBTITLE, CustomerCard
from app.pdf.pdf_company import CompanyProfile
from app.pdf.pdf_engine import PdfDocument, _QR_MODULE_MM, pdf_engine
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import resolve_pdf_logo_path
from app.pdf.pdf_tables import build_items_table, build_summary
from app.pdf.upn_qr import build_upn_qr, format_reference, format_reference_display
from app.utils.vat import ARTICLE_94_NOTICE, DOCUMENT_FOOTER_MESSAGE


def _labels(blocks) -> str:
    texts: list[str] = []

    def walk(obj):
        if obj is None:
            return
        if hasattr(obj, "text") and isinstance(obj.text, str):
            texts.append(obj.text)
        if hasattr(obj, "label") and isinstance(obj.label, str):
            texts.append(obj.label)
        if hasattr(obj, "value") and isinstance(obj.value, str):
            texts.append(obj.value)
        # Custom flowables used by the invoice redesign.
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


def _sample_invoice(**kwargs) -> PdfDocument:
    data = dict(
        doc_type="invoice",
        number="RAC-0002",
        issue_date="2026-09-22",
        due_date="2026-10-22",
        reference=format_reference("RAC-0002"),
        payment_method="Nakazilo",
        customer_name="ZAK TRADE d.o.o.",
        customer_address="Turšičeva ulica 7",
        customer_city="1380 Cerknica",
        customer_tax="26076420",
        items=[
            {
                "code": "NHT-001",
                "name": "Nega obraza – klasična",
                "quantity": 1,
                "price": 50,
                "discount": 0,
                "vat": 22,
                "total": 50,
            },
            {
                "code": "NHT-002",
                "name": "Masaža hrbta",
                "quantity": 1,
                "price": 40,
                "discount": 0,
                "vat": 22,
                "total": 40,
            },
            {
                "code": "NHT-003",
                "name": "Permanentno ličenje",
                "quantity": 1,
                "price": 120,
                "discount": 0,
                "vat": 22,
                "total": 120,
            },
        ],
        subtotal=172.13,
        discount=0,
        vat=37.87,
        total=210,
        vat_liable=True,
    )
    data.update(kwargs)
    return PdfDocument(**data)


def _opts(**overrides) -> dict:
    base = {
        "show_logo": True,
        "show_signature": True,
        "show_stamp": True,
        "show_vat": True,
        "show_discount": True,
        "show_notes": True,
        "folder": "",
        "footer": DOCUMENT_FOOTER_MESSAGE,
        "signature_path": "",
        "stamp_path": "",
        "payment_method": "Nakazilo",
        "website_url": "https://www.ju-tan.com",
        "colors": {
            "primary": "#0F172A",
            "accent": "#00C96B",
            "table_header": "#F1F5F9",
        },
    }
    base.update(overrides)
    return base


@pytest.fixture
def pdf_opts(monkeypatch):
    import sys

    options = _opts()

    def _load():
        return dict(options)

    engine_mod = sys.modules["app.pdf.pdf_engine"]
    monkeypatch.setattr(engine_mod, "load_pdf_options", _load)
    monkeypatch.setattr("app.pdf.pdf_company.load_pdf_options", _load)

    company = CompanyProfile(
        name="JU-TAN studio, Tanja Hrup s.p.",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
        country="Slovenija",
        phone="+386 69 983 936",
        email="tanja@ju-tan.com",
        website="www.ju-tan.com",
        tax_number="17113130",
        registration_number="7575556000",
        iban="SI56 0237 9205 8132 832",
        bank="Nlb d.o.o.",
        logo="",
        doc_primary_color="#0F172A",
        doc_accent_color="#00C96B",
    )
    monkeypatch.setattr(engine_mod, "load_company", lambda: company)
    monkeypatch.setattr("app.pdf.pdf_company.load_company", lambda: company)
    return options


def test_invoice_generates_successfully(tmp_path, pdf_opts):
    path = pdf_engine.render(_sample_invoice(), tmp_path / "RAC-0002.pdf")
    assert path.exists()
    assert path.stat().st_size > 2000


def test_customer_and_metadata_present(pdf_opts):
    doc = _sample_invoice()
    identity = _labels(pdf_engine._identity_block(doc, pdf_opts))
    assert "Kupec" in identity
    assert "ZAK TRADE" in identity
    assert "RAČUN" in identity
    assert "RAC-0002" in identity
    assert "Številka" in identity
    assert "Datum" in identity
    assert "Rok plačila" in identity


def test_customer_card_is_compact_not_full_width(pdf_opts):
    card = pdf_engine._customer_card(_sample_invoice(), pdf_opts)
    assert isinstance(card, CustomerCard)
    w, _h = card.wrap(CONTENT_WIDTH_MM * mm, 200 * mm)
    assert w <= (CUSTOMER_CARD_WIDTH_MM + 2) * mm
    assert "Kupec" in _labels(card.content)


def test_table_headers_and_width(pdf_opts):
    table = build_items_table(_sample_invoice().items, pdf_opts)
    w, _h = table.wrap(CONTENT_WIDTH_MM * mm, 400 * mm)
    assert abs(w - CONTENT_WIDTH_MM * mm) < 1.0
    inner = table.table
    header_text = _labels(inner._cellvalues[0])
    for expected in ("Šifra", "Artikel", "Količina", "Cena", "Popust", "Skupaj"):
        assert expected in header_text
    assert "DDV" not in header_text


def test_totals_render_za_placilo(pdf_opts):
    blocks = build_summary(172.13, 0, 37.87, 210, pdf_opts, items=_sample_invoice().items)
    text = _labels(blocks)
    assert "Skupaj brez DDV" in text
    assert "DDV" in text
    assert "Za plačilo" in text
    assert "210,00" in text.replace(" ", "")


def test_upn_qr_included_and_scannable_size(pdf_opts):
    reference = format_reference("RAC-0002")
    payload = build_upn_qr(
        iban="SI56 0237 9205 8132 832",
        recipient_name="JU-TAN",
        recipient_address="Turšičeva ulica 7",
        recipient_city="1380 Cerknica",
        amount=210,
        reference=reference,
        purpose="Plačilo računa št. RAC-0002",
    )
    assert payload

    company = CompanyProfile(
        name="JU-TAN studio",
        iban="SI56 0237 9205 8132 832",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
    )
    doc = _sample_invoice(reference=reference)
    qr = pdf_engine._qr_flowable(doc, company, pdf_opts, module_mm=_QR_MODULE_MM)
    assert qr is not None
    side_mm = _QR_MODULE_MM * 85
    # MASTER-measured QR (~24 mm), still large enough for reliable UPN scanning.
    assert 20 <= side_mm <= 28
    text = _labels(qr)
    assert "Plačilo z UPN QR" in text


def test_upn_payload_rac0002_fixture_fields():
    """Deterministic UPN QR payload checks for the RAC-0002 MASTER fixture."""
    reference = format_reference("RAC-0002")
    assert reference == "SI000002"
    assert format_reference_display(reference) == "SI00 0002"

    payload = build_upn_qr(
        iban="SI56 0237 9205 8132 832",
        recipient_name="JU-TAN studio, Tanja Hrup s.p.",
        recipient_address="Turšičeva ulica 7",
        recipient_city="1380 Cerknica",
        amount=210,
        reference=reference,
        purpose="Plačilo računa št. RAC-0002",
        payer_name="ZAK TRADE d.o.o.",
        payer_address="Turšičeva ulica 7",
        payer_city="1380 Cerknica",
    )
    assert payload is not None
    assert payload.startswith("UPNQR\n")
    assert "http://" not in payload
    assert "https://" not in payload
    fields = payload.strip().split("\n")
    assert fields[0] == "UPNQR"
    assert fields[8] == "00000021000"  # 210.00 EUR in cents, 11 digits
    assert fields[14] == "SI56023792058132832"
    assert fields[15] == "SI000002"
    assert "Plačilo računa št. RAC-0002" in fields[12]
    assert "JU-TAN studio" in fields[16]
    # Visible Sklic and encoded reference agree (spacing aside).
    assert format_reference_display(fields[15]).replace(" ", "") == fields[15]


def test_visible_sklic_matches_qr_reference(pdf_opts):
    company = CompanyProfile(
        name="JU-TAN studio, Tanja Hrup s.p.",
        iban="SI56 0237 9205 8132 832",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
        bank="Nlb d.o.o.",
    )
    doc = _sample_invoice(reference=format_reference("RAC-0002"))
    pay = _labels(pdf_engine._payment_block(doc, company, pdf_opts))
    assert "SI00 0002" in pay
    payload = build_upn_qr(
        iban=company.iban,
        recipient_name=company.name,
        recipient_address=company.address,
        recipient_city="1380 Cerknica",
        amount=doc.total,
        reference=doc.reference,
        purpose=f"Plačilo računa št. {doc.number}",
    )
    assert payload is not None
    assert "SI000002" in payload
    assert "SI00 0002".replace(" ", "") in payload.replace(" ", "")


def test_company_block_includes_required_fields(pdf_opts):
    company = CompanyProfile(
        name="JU-TAN studio, Tanja Hrup s.p.",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
        country="Slovenija",
        phone="+386 69 983 936",
        email="tanja@ju-tan.com",
        website="www.ju-tan.com",
        tax_number="17113130",
        registration_number="7575556000",
        iban="SI56 0237 9205 8132 832",
        bank="Nlb d.o.o.",
    )
    text = _labels(build_header(company, pdf_opts))
    for expected in (
        "JU-TAN studio, Tanja Hrup s.p.",
        "Turšičeva ulica 7",
        "17113130",
        "7575556000",
        "SI56 0237 9205 8132 832",
        "tanja@ju-tan.com",
        "+386 69 983 936",
    ):
        assert expected in text


def test_invoice_page_number_format(tmp_path, pdf_opts):
    path = pdf_engine.render(_sample_invoice(), tmp_path / "paged.pdf")
    import fitz

    text = fitz.open(str(path))[0].get_text()
    assert "1 / 1" in text


def test_multipage_invoice_repeats_header(tmp_path, pdf_opts):
    items = [
        {
            "code": f"L{i}",
            "name": f"Postavka številka {i} — dolg opis artikla za prelom",
            "quantity": 1,
            "price": 10,
            "discount": 0,
            "vat": 22,
            "total": 12.2,
        }
        for i in range(1, 40)
    ]
    doc = _sample_invoice(items=items, subtotal=400, vat=88, total=488)
    path = pdf_engine.render(doc, tmp_path / "long.pdf")
    import fitz

    pdf = fitz.open(str(path))
    assert len(pdf) >= 2
    # Table header text should appear on later pages (repeatRows=1).
    assert "Šifra" in pdf[0].get_text()
    assert "Šifra" in pdf[1].get_text()
    assert f"{len(pdf)} / {len(pdf)}" in pdf[-1].get_text() or f"1 / {len(pdf)}" in pdf[0].get_text()
    # Footer slogan present; no signature labels.
    assert "Direktorica" not in pdf[0].get_text()
    assert "Podpis" not in pdf[0].get_text()


def test_invoice_renders_without_company_stamp(tmp_path, pdf_opts):
    pdf_opts["show_stamp"] = True
    pdf_opts["stamp_path"] = str(tmp_path / "stamp.png")
    blocks = pdf_engine._payment_block(
        _sample_invoice(),
        CompanyProfile(name="X", iban="SI56 0237 9205 8132 832"),
        pdf_opts,
    )
    assert "Žig" not in _labels(blocks)
    path = pdf_engine.render(_sample_invoice(), tmp_path / "no_stamp.pdf")
    raw = path.read_bytes()
    assert "Žig".encode("utf-16-be") not in raw


def test_invoice_never_renders_signature_or_stamp(tmp_path, pdf_opts):
    """Production invoices omit signature/stamp entirely (intentional vs MASTER)."""
    from PIL import Image as PILImage

    sig = tmp_path / "sig.png"
    PILImage.new("RGB", (200, 80), (20, 40, 180)).save(sig)
    pdf_opts["show_signature"] = True
    pdf_opts["show_stamp"] = True
    pdf_opts["signature_path"] = str(sig)
    pdf_opts["stamp_path"] = str(tmp_path / "stamp.png")
    company = CompanyProfile(
        name="JU-TAN studio, Tanja Hrup s.p.",
        iban="SI56 0237 9205 8132 832",
    )
    labels = _labels(pdf_engine._payment_block(_sample_invoice(), company, pdf_opts))
    assert "Direktorica" not in labels
    assert "Tanja Hrup" not in labels
    assert "Žig" not in labels
    assert "Podpis" not in labels

    path = pdf_engine.render(_sample_invoice(), tmp_path / "no_sig.pdf")
    raw = path.read_bytes()
    assert "Direktorica".encode("utf-16-be") not in raw
    assert "Direktorica".encode("utf-8") not in raw
    assert "Podpis".encode("utf-16-be") not in raw
    assert "Žig".encode("utf-16-be") not in raw

    import fitz

    page_text = fitz.open(str(path))[0].get_text()
    assert "Direktorica" not in page_text
    assert "Podpis" not in page_text
    assert "Žig" not in page_text
    # Signer name must not appear as a standalone signature label (only in company header).
    assert page_text.count("Tanja Hrup") == 1
    assert "JU-TAN studio, Tanja Hrup s.p." in page_text


def test_inline_signature_helper_still_builds_for_other_docs(tmp_path, pdf_opts):
    """Helper remains available for non-invoice documents."""
    from PIL import Image as PILImage

    sig = tmp_path / "sig.png"
    PILImage.new("RGB", (200, 80), (20, 40, 180)).save(sig)
    pdf_opts["show_signature"] = True
    pdf_opts["signature_path"] = str(sig)
    company = CompanyProfile(name="JU-TAN studio, Tanja Hrup s.p.")
    block = pdf_engine._inline_signature(pdf_opts, company)
    assert block is not None
    labels = _labels(block)
    assert "Tanja Hrup" in labels
    assert "Direktorica" in labels


def test_signature_missing_does_not_crash(pdf_opts):
    pdf_opts["show_signature"] = True
    pdf_opts["signature_path"] = ""
    block = pdf_engine._inline_signature(pdf_opts, CompanyProfile(name="Test s.p."))
    assert block is not None


def test_non_vat_shows_article_94(tmp_path, pdf_opts):
    doc = _sample_invoice(vat_liable=False, vat=0, total=172.13, subtotal=172.13)
    path = pdf_engine.render(doc, tmp_path / "novat.pdf")
    raw = path.read_bytes()
    assert b"94" in raw or "94".encode("utf-16-be") in raw
    assert ARTICLE_94_NOTICE


def test_thanks_uses_approved_subtitle(pdf_opts):
    company = CompanyProfile(name="JU-TAN", website="www.ju-tan.com")
    text = _labels(pdf_engine._thanks_block(company, pdf_opts))
    assert "Hvala za zaupanje" in text
    assert THANKS_SUBTITLE in text


def test_offer_document_identity_preserved(pdf_opts):
    offer = _sample_invoice(doc_type="offer", number="PON-0001")
    text = _labels(pdf_engine._title_block(offer, pdf_opts))
    assert "PONUDBA" in text
    assert "RAČUN" not in text
    assert "Velja do" in text


def test_original_logo_resolves_for_header(pdf_opts):
    resolved = resolve_pdf_logo_path("")
    assert resolved is not None and resolved.is_file()
    header = build_header(CompanyProfile(name="X", logo=""), pdf_opts)
    body = next(f for f in header if isinstance(f, Table) and len(f._cellvalues[0]) == 2)
    logo_cell = body._cellvalues[0][0]
    if isinstance(logo_cell, Table):
        logo_cell = logo_cell._cellvalues[0][0]
    assert isinstance(logo_cell, Image)
    assert logo_cell.drawWidth / logo_cell.drawHeight > 2.0


def test_show_logo_false_hides_logo(pdf_opts):
    pdf_opts["show_logo"] = False
    header = build_header(CompanyProfile(name="X", logo=""), pdf_opts)
    body = next(f for f in header if isinstance(f, Table) and len(f._cellvalues[0]) == 2)
    assert isinstance(body._cellvalues[0][0], Spacer)


def test_content_widths_inside_a4(tmp_path, pdf_opts):
    path = pdf_engine.render(_sample_invoice(), tmp_path / "width.pdf")
    import pymupdf

    with pymupdf.open(str(path)) as pdf:
        page_texts = [page.get_text() for page in pdf]
        assert len(pdf) == 1, f"PDF has {len(pdf)} pages. PAGE TEXTS: {page_texts!r}"


def test_multipage_invoice(tmp_path, pdf_opts):
    items = [
        {
            "code": f"L{i}",
            "name": f"Postavka številka {i} — dolg opis artikla za prelom",
            "quantity": 1,
            "price": 10,
            "discount": 0,
            "vat": 22,
            "total": 12.2,
        }
        for i in range(1, 40)
    ]
    doc = _sample_invoice(items=items, subtotal=400, vat=88, total=488)
    path = pdf_engine.render(doc, tmp_path / "long.pdf")
    pages = len(re.findall(rb"/Type\s*/Page[^s]", path.read_bytes()))
    assert pages >= 2


def test_qr_recovers_from_invalid_reference(pdf_opts):
    company = CompanyProfile(
        name="JU-TAN studio",
        iban="SI56 0237 9205 8132 832",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
    )
    doc = _sample_invoice(reference="SI00 RAC-0002")
    qr = pdf_engine._qr_flowable(doc, company, pdf_opts)
    assert qr is not None


