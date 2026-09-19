"""Regression: invoice UI must stay responsive (no stylesheet freeze)."""

from __future__ import annotations

import time

import pytest

from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.payment_repository import payment_repository
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.modules.invoices.invoice_page import InvoicePage
from app.modules.payments.payment_page import PaymentPage
from app.modules.settings.settings_controller import SettingsController
from app.theme.theme import theme_manager


@pytest.fixture
def paid_invoice(qt_app):
    import uuid

    tag = uuid.uuid4().hex[:8]
    customer_repository.add(
        f"Freeze Test {tag} d.o.o.", "Test", "", "", "Ljubljana", "SI", "", "", ""
    )
    cid = customer_repository.search(f"Freeze Test {tag}")[0][0]
    number = f"RAC-FZ-{tag}"
    iid = invoice_repository.add(
        number,
        cid,
        "2026-09-19",
        "2026-10-19",
        100,
        0,
        0,
        100,
        "",
        "Izdan",
        False,
    )
    invoice_repository.add_item(
        invoice_id=iid,
        article_id=None,
        code="T1",
        name="Storitev",
        description="",
        quantity=1,
        unit="kos",
        price=100,
        discount=0,
        vat=0,
        total=100,
    )
    payment_repository.add(iid, "2026-09-19", 40, "Nakazilo")
    payment_repository.sync_invoice_status(iid, 100)
    payment_repository.add(iid, "2026-09-19", 60, "Kompenzacija")
    status = payment_repository.sync_invoice_status(iid, 100)
    assert status == "Plačan"
    notes = (
        "[PLAČILO] 2026-09-19 · Nakazilo · 40.00 €\n"
        "[PLAČILO] 2026-09-19 · Kompenzacija · 60.00 €"
    )
    invoice_repository.update_notes(iid, notes)
    return iid


def test_paid_invoice_open_close_stress_with_heartbeat(qt_app, paid_invoice):
    heartbeats: list[float] = []
    last = time.perf_counter()

    def beat() -> None:
        nonlocal last
        now = time.perf_counter()
        heartbeats.append((now - last) * 1000)
        last = now

    from PySide6.QtCore import QTimer

    timer = QTimer()
    timer.setInterval(50)
    timer.timeout.connect(beat)
    timer.start()

    open_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        dlg = InvoiceDialog(None, invoice_id=paid_invoice)
        dlg.show()
        qt_app.processEvents()
        assert not dlg.btn_save.isEnabled()
        assert not dlg.notes.isEnabled()
        dlg.close()
        dlg.deleteLater()
        qt_app.processEvents()
        open_ms.append((time.perf_counter() - t0) * 1000)

    timer.stop()
    assert max(open_ms) < 2000, f"invoice open blocked UI: {max(open_ms):.0f}ms"
    assert heartbeats, "heartbeat did not run"
    assert max(heartbeats) < 2000, f"UI heartbeat stall: {max(heartbeats):.0f}ms"


def test_invoice_payment_navigation_stress(qt_app, paid_invoice):
    inv = InvoicePage()
    pay = PaymentPage()
    cycle_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        inv.refresh()
        qt_app.processEvents()
        pay.refresh()
        qt_app.processEvents()
        inv.refresh()
        qt_app.processEvents()
        cycle_ms.append((time.perf_counter() - t0) * 1000)
    assert max(cycle_ms) < 2000, f"nav cycle blocked UI: {max(cycle_ms):.0f}ms"


def test_theme_apply_deferred_while_invoice_modal_open(qt_app, paid_invoice):
    """Root-cause regression: setStyleSheet under InvoiceDialog must not run."""
    ctrl = SettingsController()
    ctrl.apply_appearance(qt_app)
    before = theme_manager._last_stylesheet

    dlg = InvoiceDialog(None, invoice_id=paid_invoice)
    dlg.setModal(True)
    dlg.open()
    qt_app.processEvents()
    assert qt_app.activeModalWidget() is dlg

    t0 = time.perf_counter()
    # Force a different accent so stylesheet content would change if applied.
    extras = ctrl.load_extras()
    extras["appearance"] = {
        **extras.get("appearance", {}),
        "accent": "orange" if extras.get("appearance", {}).get("accent") != "orange" else "blue",
    }
    ctrl.save_extras(extras)
    applied_flag = []
    original_set = qt_app.setStyleSheet

    def probe(ss: str) -> None:
        applied_flag.append(True)
        original_set(ss)

    qt_app.setStyleSheet = probe  # type: ignore[method-assign]
    try:
        for _ in range(8):
            ctrl.apply_appearance(qt_app)
            qt_app.processEvents()
        elapsed = (time.perf_counter() - t0) * 1000
    finally:
        qt_app.setStyleSheet = original_set  # type: ignore[method-assign]

    assert not applied_flag, "setStyleSheet must be deferred while invoice modal is open"
    assert elapsed < 1500, f"deferred theme path still blocked UI: {elapsed:.0f}ms"
    dlg.close()
    qt_app.processEvents()
    # Flush deferred apply
    for _ in range(20):
        qt_app.processEvents()
        time.sleep(0.05)
    # After modal closes, deferred apply may run — must remain responsive.
    assert theme_manager._last_stylesheet is not None
    _ = before


def test_overpayment_still_rejected(paid_invoice):
    with pytest.raises(ValueError):
        payment_repository.add(paid_invoice, "2026-09-19", 99999.0, "Nakazilo")
