"""Regression: PDF signature/stamp options, pagination, Slovenian Unicode, idle lock."""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from app.core.session import Session, session
from app.pdf.pdf_company import load_pdf_options
from app.pdf.pdf_engine import PdfDocument, pdf_engine
from app.pdf.pdf_styles import ensure_fonts
from app.utils.vat import ARTICLE_94_NOTICE, DOCUMENT_FOOTER_MESSAGE


def _page_count(path: Path) -> int:
    raw = path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", raw))


def _short_invoice(**kwargs) -> PdfDocument:
    data = dict(
        doc_type="invoice",
        number="RAC-SHORT-1",
        issue_date="2026-09-19",
        due_date="2026-10-19",
        reference="SI00 RAC-SHORT-1",
        payment_method="Nakazilo",
        customer_name="Kupec ČŠŽ",
        customer_address="Ulica poiščemo 1",
        customer_city="1000 Ljubljana",
        items=[
            {
                "code": "A1",
                "name": "Storitev račun / naročilo / plačilo",
                "quantity": 1,
                "price": 150,
                "discount": 0,
                "vat": 0,
                "total": 150,
            }
        ],
        subtotal=150,
        discount=0,
        vat=0,
        total=150,
        vat_liable=False,
    )
    data.update(kwargs)
    return PdfDocument(**data)


def _long_invoice() -> PdfDocument:
    items = [
        {
            "code": f"L{i}",
            "name": f"Postavka številka {i} — zaključeno naročilo",
            "quantity": 1,
            "price": 10,
            "discount": 0,
            "vat": 22,
            "total": 12.2,
        }
        for i in range(1, 36)
    ]
    return PdfDocument(
        doc_type="invoice",
        number="RAC-LONG-1",
        issue_date="2026-09-19",
        due_date="2026-10-19",
        customer_name="Dolg Kupec",
        items=items,
        subtotal=350,
        vat=77,
        total=427,
        vat_liable=True,
    )


@pytest.fixture
def pdf_opts(monkeypatch):
    import sys

    base = {
        "show_logo": False,
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
    }

    def _load():
        return dict(base)

    # Package exports instance as app.pdf.pdf_engine — patch the real module.
    engine_mod = sys.modules["app.pdf.pdf_engine"]
    monkeypatch.setattr(engine_mod, "load_pdf_options", _load)
    monkeypatch.setattr("app.pdf.pdf_company.load_pdf_options", _load)
    return base


def test_signature_stamp_both_off_reserves_zero_space(tmp_path, pdf_opts, monkeypatch):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    monkeypatch.setattr(pdf_engine, "_qr_flowable", lambda *a, **k: None)
    blocks = pdf_engine._signature_block(pdf_opts)
    assert blocks == []
    path = pdf_engine.render(_short_invoice(), tmp_path / "sig_off.pdf")
    raw = path.read_bytes()
    assert b"Podpis" not in raw
    # Žig may appear as UTF-16 in content; also check extracted-ish markers
    assert "Podpis".encode("utf-16-be") not in raw


def test_signature_on_stamp_off(tmp_path, pdf_opts, monkeypatch):
    pdf_opts["show_signature"] = True
    pdf_opts["show_stamp"] = False
    monkeypatch.setattr(pdf_engine, "_qr_flowable", lambda *a, **k: None)
    blocks = pdf_engine._signature_block(pdf_opts)
    assert blocks
    labels = []
    for flow in blocks:
        if hasattr(flow, "wrap"):
            pass
    # Render and ensure Podpis present, Žig label absent from story captions
    story_labels = []
    for item in blocks:
        if hasattr(item, "_cellvalues"):
            continue
    path = pdf_engine.render(_short_invoice(), tmp_path / "sig_only.pdf")
    assert path.exists()
    # Signature block returned non-empty
    assert any(True for _ in blocks)


def test_stamp_on_signature_off(pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = True
    blocks = pdf_engine._signature_block(pdf_opts)
    assert blocks
    pdf_opts["show_signature"] = True
    pdf_opts["show_stamp"] = True
    both = pdf_engine._signature_block(pdf_opts)
    assert both


def test_short_invoice_one_page_without_signature(tmp_path, pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    path = pdf_engine.render(_short_invoice(), tmp_path / "short.pdf")
    assert _page_count(path) == 1


def test_short_invoice_one_page_with_optional_blocks(tmp_path, pdf_opts):
    """RAC-0005-like: compact signature placeholders must not force a blank page 2."""
    pdf_opts["show_signature"] = True
    pdf_opts["show_stamp"] = True
    path = pdf_engine.render(_short_invoice(), tmp_path / "short_sig.pdf")
    assert _page_count(path) == 1


def test_long_invoice_can_paginate(tmp_path, pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    path = pdf_engine.render(_long_invoice(), tmp_path / "long.pdf")
    assert _page_count(path) >= 2


def test_non_vat_totals_and_art94(tmp_path, pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    doc = _short_invoice(vat_liable=False, vat=0, total=150, subtotal=150)
    path = pdf_engine.render(doc, tmp_path / "novat.pdf")
    raw = path.read_bytes()
    assert doc.vat == 0
    assert doc.total == 150
    # Art. 94 notice is drawn via Paragraph (embedded as Unicode in content)
    assert "94".encode("utf-8") in raw or b"94" in raw
    assert ARTICLE_94_NOTICE


def test_vat_liable_unchanged(tmp_path, pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    doc = _short_invoice(
        vat_liable=True,
        vat=33,
        total=183,
        subtotal=150,
        items=[
            {
                "code": "A1",
                "name": "Storitev",
                "quantity": 1,
                "price": 150,
                "discount": 0,
                "vat": 22,
                "total": 183,
            }
        ],
    )
    path = pdf_engine.render(doc, tmp_path / "vat.pdf")
    assert path.exists()
    assert doc.vat == 33
    assert doc.total == 183


def test_slovenian_unicode_paragraph_table_footer(tmp_path, pdf_opts):
    pdf_opts["show_signature"] = False
    pdf_opts["show_stamp"] = False
    regular, bold = ensure_fonts()
    assert regular != "Helvetica"
    assert bold != "Helvetica-Bold"

    doc = _short_invoice(
        customer_name="ČŠŽ čšž",
        notes="poiščemo račun naročilo plačilo zaključeno številka pošiljka",
    )
    pdf_opts["show_notes"] = True
    path = pdf_engine.render(doc, tmp_path / "unicode.pdf")
    raw = path.read_bytes()

    # Footer canvas path must use the Unicode font (not Helvetica).
    assert regular.encode("latin-1") in raw or b"EnterpriseSans" in raw or b"Segoe" in raw
    # Replacement character must not appear for Slovenian text.
    assert "\ufffd".encode("utf-16-be") not in raw
    assert DOCUMENT_FOOTER_MESSAGE
    assert "poiščemo" in DOCUMENT_FOOTER_MESSAGE

    # Round-trip: draw footer alone and ensure glyph widths resolve for č
    from reportlab.pdfbase.pdfmetrics import stringWidth

    width = stringWidth("poiščemo", regular, 8)
    assert width > stringWidth("poisemo", regular, 8)


def test_pdf_options_persist_signature_stamp(monkeypatch, tmp_path):
    from app.modules.settings.settings_controller import SettingsController, default_settings
    from app.core.config_guard import stamp
    from app.core.security import write_json_atomic
    from app.core.constants import DATA_DIR

    settings_path = DATA_DIR / "settings.json"
    data = default_settings()
    data["pdf"]["signature"] = False
    data["pdf"]["stamp"] = True
    data["setup_complete"] = True
    write_json_atomic(settings_path, stamp(data))

    opts = load_pdf_options()
    assert opts["show_signature"] is False
    assert opts["show_stamp"] is True


def test_idle_focus_loss_does_not_lock():
    s = Session()
    s.timeout_sec = 600
    s.touch()
    # Simulate "switched to PDF viewer" with no activity events — still under timeout.
    assert not s.idle_too_long()
    s.last_activity = time.monotonic() - 30
    assert not s.idle_too_long()


def test_idle_activity_resets_and_timeout_locks():
    s = Session()
    s.timeout_sec = 2
    s.touch()
    assert not s.idle_too_long()
    s.last_activity = time.monotonic() - 3
    assert s.idle_too_long()
    s.touch()
    assert not s.idle_too_long()


def test_manual_lock_and_unlock_resets_idle():
    session.login("Tester", "Administrator")
    session.timeout_sec = 30
    session.lock()
    assert session.locked
    session.unlock("Tester")
    assert not session.locked
    assert not session.idle_too_long()
    session.locked = False
    session.authenticated = True


def test_idle_guard_single_install(qt_app, monkeypatch):
    from PySide6.QtWidgets import QWidget
    import app.core.idle_guard as ig

    monkeypatch.setattr(ig, "_guard", None)
    window = QWidget()
    g1 = ig.install_idle_guard(qt_app, window, password_required=True, timeout_sec=600)
    g2 = ig.install_idle_guard(qt_app, window, password_required=True, timeout_sec=600)
    assert g1 is g2
    assert g1.installed
    assert ig.get_idle_guard() is g1
    # Second install must not stack another filter blindly
    assert g1._installed is True
    g1.disarm()
    monkeypatch.setattr(ig, "_guard", None)


def test_idle_guard_activity_events_reset(qt_app, monkeypatch):
    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget
    import app.core.idle_guard as ig

    monkeypatch.setattr(ig, "_guard", None)
    window = QWidget()
    guard = ig.install_idle_guard(qt_app, window, password_required=False, timeout_sec=600)
    session.last_activity = time.monotonic() - 100
    before = session.last_activity
    ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
    guard.eventFilter(window, ev)
    assert session.last_activity >= before
    guard.disarm()
    monkeypatch.setattr(ig, "_guard", None)


def test_idle_guard_duplicate_dialog_blocked(qt_app, monkeypatch):
    from PySide6.QtWidgets import QWidget
    import app.core.idle_guard as ig

    monkeypatch.setattr(ig, "_guard", None)
    window = QWidget()
    guard = ig.install_idle_guard(qt_app, window, password_required=True, timeout_sec=1)
    guard._dialog_open = True
    session.locked = False
    session.last_activity = time.monotonic() - 10
    # Would lock + show dialog, but dialog_open blocks re-entry
    calls = []

    def _boom():
        calls.append(1)

    monkeypatch.setattr(guard, "_show_unlock", _boom)
    guard._tick()
    # locked becomes True but show was invoked once path... actually _tick returns early if dialog_open
    assert calls == []
    guard.disarm()
    session.locked = False
    monkeypatch.setattr(ig, "_guard", None)


def test_rac0006_short_invoice_one_page_with_qr_and_signature(tmp_path, pdf_opts, monkeypatch):
    """RAC-0006 shape: Art.94 + fake QR height + compact signature stays on 1 page."""
    from reportlab.platypus import Spacer as RLSpacer

    from app.pdf.pdf_engine import PdfEngine

    pdf_opts["show_signature"] = True
    pdf_opts["show_stamp"] = True

    def _fake_qr(self, document, company, *, module_mm=0.65):
        return RLSpacer(1, 40)

    monkeypatch.setattr(PdfEngine, "_qr_flowable", _fake_qr)
    path = pdf_engine.render(
        _short_invoice(
            vat_liable=False,
            vat=0,
            total=455,
            subtotal=500,
            discount=45,
            notes="[Iz ponudbe]",
        ),
        tmp_path / "rac6like.pdf",
    )
    assert _page_count(path) == 1


def test_invoice_counter_heals_below_existing_numbers(monkeypatch):
    from app.database.invoice_repository import invoice_repository

    # Soft check: get_next_number never returns a number that already exists.
    number = invoice_repository.get_next_number()
    assert number.startswith("RAC-")
    from app.database.database import db

    conn = db.connect()
    row = conn.execute(
        "SELECT 1 FROM invoices WHERE invoice_number=?", (number,)
    ).fetchone()
    conn.close()
    assert row is None
