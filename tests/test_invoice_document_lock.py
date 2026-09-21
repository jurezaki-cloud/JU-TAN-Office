"""Regression: invoice document edit lock by status."""

from __future__ import annotations

import uuid

import pytest

from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.modules.invoices.invoice_dialog import (
    InvoiceDialog,
    invoice_is_editable,
    invoice_lock_message,
)


def _seed_invoice(status: str) -> tuple[int, int]:
    tag = uuid.uuid4().hex[:8]
    customer_repository.add(
        f"Lock Test {tag} d.o.o.", "Test", "", "", "Ljubljana", "SI", "", "", ""
    )
    cid = customer_repository.search(f"Lock Test {tag}")[0][0]
    iid = invoice_repository.add(
        f"RAC-LOCK-{tag}",
        cid,
        "2026-09-19",
        "2026-10-19",
        100,
        0,
        0,
        100,
        "",
        status,
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
    return iid, cid


def _assert_editable(dlg: InvoiceDialog) -> None:
    assert dlg.read_only is False
    assert dlg.btn_save.isEnabled()
    assert dlg.notes.isEnabled()
    assert dlg.customer.isEnabled()
    assert dlg.issue_date.isEnabled()
    assert dlg.due_date.isEnabled()
    assert dlg.btn_add_item.isEnabled()
    assert dlg.btn_remove_item.isEnabled()
    assert not dlg.lock_notice.isVisible()


def _assert_locked(dlg: InvoiceDialog, *, status: str) -> None:
    assert dlg.read_only is True
    assert not dlg.btn_save.isEnabled()
    assert not dlg.notes.isEnabled()
    assert not dlg.customer.isEnabled()
    assert not dlg.issue_date.isEnabled()
    assert not dlg.due_date.isEnabled()
    assert not dlg.btn_add_item.isEnabled()
    assert not dlg.btn_remove_item.isEnabled()
    assert dlg.lock_notice.isVisible()
    assert invoice_lock_message(status) in dlg.lock_notice.text()
    assert "Pregled računa" in dlg.windowTitle()


@pytest.mark.parametrize(
    "status,editable",
    [
        ("Osnutek", True),
        ("Izdan", False),
        ("Plačan", False),
        ("Storniran", False),
    ],
)
def test_invoice_is_editable_helper(status, editable):
    assert invoice_is_editable(status) is editable


def test_draft_invoice_remains_editable(qt_app):
    iid, cid = _seed_invoice("Osnutek")
    try:
        dlg = InvoiceDialog(None, invoice_id=iid)
        dlg.show()
        qt_app.processEvents()
        _assert_editable(dlg)
        dlg.close()
    finally:
        invoice_repository.delete(iid)
        customer_repository.delete(cid)


def test_issued_invoice_is_locked(qt_app):
    iid, cid = _seed_invoice("Izdan")
    try:
        dlg = InvoiceDialog(None, invoice_id=iid)
        dlg.show()
        qt_app.processEvents()
        _assert_locked(dlg, status="Izdan")
        dlg.close()
    finally:
        invoice_repository.delete(iid)
        customer_repository.delete(cid)


def test_paid_invoice_is_locked(qt_app):
    iid, cid = _seed_invoice("Plačan")
    try:
        dlg = InvoiceDialog(None, invoice_id=iid)
        dlg.show()
        qt_app.processEvents()
        _assert_locked(dlg, status="Plačan")
        dlg.close()
    finally:
        invoice_repository.delete(iid)
        customer_repository.delete(cid)


def test_cancelled_invoice_is_locked(qt_app):
    iid, cid = _seed_invoice("Storniran")
    try:
        dlg = InvoiceDialog(None, invoice_id=iid)
        dlg.show()
        qt_app.processEvents()
        _assert_locked(dlg, status="Storniran")
        dlg.close()
    finally:
        invoice_repository.delete(iid)
        customer_repository.delete(cid)
