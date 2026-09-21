"""GOLD-2/3A/3B: concurrent numbering + transactional create/edit."""

from __future__ import annotations

import sqlite3
import threading
from datetime import date

import pytest

from app.database.customer_repository import customer_repository
from app.database.database import db
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.database.travel_order_repository import travel_order_repository
from app.modules.purchase.purchase_repository import purchase_repository
from app.modules.suppliers.suppliers_repository import suppliers_repository


TODAY = date.today().isoformat()


def _customer_id() -> int:
    customer_repository.add(
        "TX-RACE d.o.o.", "QA", "Ulica 1", "1000", "Ljubljana", "SI", "", "tx@t.si", "",
    )
    return int(customer_repository.search("TX-RACE d.o.o.")[0][0])


def _supplier_id() -> int:
    suppliers_repository.ensure_schema()
    suppliers_repository.add("TX Supplier", "", "Kontakt", "", "", "Active", "")
    rows = suppliers_repository.get_all()
    return int(rows[0][0])


def _sample_item(**overrides) -> dict:
    item = {
        "article_id": None,
        "code": "A1",
        "name": "Artikel",
        "description": "",
        "quantity": 1,
        "unit": "kos",
        "price": 10,
        "discount": 0,
        "vat": 22,
        "total": 12.2,
    }
    item.update(overrides)
    return item


def _po_item(**overrides) -> dict:
    item = {
        "article_id": None,
        "code": "P1",
        "name": "Nabava",
        "quantity": 1,
        "qty_received": 0,
        "price": 10,
        "vat": 22,
        "total": 12.2,
    }
    item.update(overrides)
    return item


def _run_two(worker):
    barrier = threading.Barrier(2)
    results: list = []
    errors: list[BaseException] = []

    def run():
        try:
            barrier.wait(timeout=10)
            results.append(worker())
        except BaseException as exc:  # noqa: BLE001 — collect for assertion
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
        assert not thread.is_alive()
    assert errors == [], errors
    assert len(results) == 2
    return results


def test_concurrent_invoice_allocate_and_insert():
    customer_id = _customer_id()
    invoice_repository.ensure_schema()

    def worker():
        with db.transaction(immediate=True) as conn:
            number = invoice_repository.allocate_next_number(conn)
            invoice_id = invoice_repository.add(
                invoice_number=number,
                customer_id=customer_id,
                issue_date=TODAY,
                due_date=TODAY,
                subtotal=10,
                discount=0,
                vat=2.2,
                total=12.2,
                notes="concurrent",
                status="Izdan",
                conn=conn,
            )
        return number, invoice_id

    numbers = [row[0] for row in _run_two(worker)]
    assert numbers[0] != numbers[1]
    assert len(set(numbers)) == 2


def test_concurrent_offer_create_allocates_unique_numbers():
    customer_id = _customer_id()

    def worker():
        offer_id = offer_repository.create(
            None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
        )
        return offer_repository.get_by_id(offer_id)[1]

    numbers = _run_two(worker)
    assert numbers[0] != numbers[1]
    assert len(set(numbers)) == 2


def test_concurrent_order_create_allocates_unique_numbers():
    customer_id = _customer_id()
    order_repository.ensure_schema()

    def worker():
        order_id = order_repository.create(
            None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
        )
        return order_repository.get_by_id(order_id)[1]

    numbers = _run_two(worker)
    assert numbers[0] != numbers[1]
    assert len(set(numbers)) == 2


def test_concurrent_purchase_create_allocates_unique_numbers():
    supplier_id = _supplier_id()
    purchase_repository.ensure_schema()

    def worker():
        purchase_id = purchase_repository.create(
            None, supplier_id, TODAY, TODAY, "Draft", 10, 2.2, 12.2, "",
        )
        return purchase_repository.get_by_id(purchase_id)[1]

    numbers = _run_two(worker)
    assert numbers[0] != numbers[1]
    assert len(set(numbers)) == 2


def test_invoice_create_with_items_rolls_back_on_item_failure(monkeypatch):
    customer_id = _customer_id()
    invoice_repository.ensure_schema()
    before = len(invoice_repository.get_all())

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated item insert failure")

    monkeypatch.setattr(invoice_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated item insert failure"):
        invoice_repository.create_with_items(
            customer_id=customer_id,
            issue_date=TODAY,
            due_date=TODAY,
            subtotal=10,
            discount=0,
            vat=2.2,
            total=12.2,
            notes="orphan-check",
            items=[_sample_item()],
        )

    assert len(invoice_repository.get_all()) == before


def test_offer_create_with_items_rolls_back_on_item_failure(monkeypatch):
    customer_id = _customer_id()
    before_ids = {row[0] for row in offer_repository.get_all()}

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated item insert failure")

    monkeypatch.setattr(offer_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated item insert failure"):
        offer_repository.create_with_items(
            None,
            customer_id,
            TODAY,
            TODAY,
            "Osnutek",
            10,
            0,
            2.2,
            12.2,
            "",
            [_sample_item()],
        )

    after_ids = {row[0] for row in offer_repository.get_all()}
    assert after_ids == before_ids


def test_order_create_with_items_rolls_back_on_item_failure(monkeypatch):
    customer_id = _customer_id()
    order_repository.ensure_schema()
    before_ids = {row[0] for row in order_repository.get_all()}

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated item insert failure")

    monkeypatch.setattr(order_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated item insert failure"):
        order_repository.create_with_items(
            None,
            customer_id,
            TODAY,
            TODAY,
            "Osnutek",
            10,
            0,
            2.2,
            12.2,
            "",
            [_sample_item()],
        )

    after_ids = {row[0] for row in order_repository.get_all()}
    assert after_ids == before_ids


def test_purchase_create_with_items_rolls_back_on_item_failure(monkeypatch):
    supplier_id = _supplier_id()
    purchase_repository.ensure_schema()
    before_ids = {row[0] for row in purchase_repository.get_all()}

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated item insert failure")

    monkeypatch.setattr(purchase_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated item insert failure"):
        purchase_repository.create_with_items(
            None,
            supplier_id,
            TODAY,
            TODAY,
            "Draft",
            10,
            2.2,
            12.2,
            "",
            [_po_item()],
        )

    after_ids = {row[0] for row in purchase_repository.get_all()}
    assert after_ids == before_ids


def test_create_with_items_rejects_empty_items():
    customer_id = _customer_id()
    supplier_id = _supplier_id()
    invoice_repository.ensure_schema()
    order_repository.ensure_schema()
    purchase_repository.ensure_schema()

    with pytest.raises(ValueError, match="postavko"):
        invoice_repository.create_with_items(
            customer_id=customer_id,
            issue_date=TODAY,
            due_date=TODAY,
            subtotal=0,
            discount=0,
            vat=0,
            total=0,
            notes="",
            items=[],
        )
    with pytest.raises(ValueError, match="postavko"):
        offer_repository.create_with_items(
            None, customer_id, TODAY, TODAY, "Osnutek", 0, 0, 0, 0, "", [],
        )
    with pytest.raises(ValueError, match="postavko"):
        order_repository.create_with_items(
            None, customer_id, TODAY, TODAY, "Osnutek", 0, 0, 0, 0, "", [],
        )
    with pytest.raises(ValueError, match="postavko"):
        purchase_repository.create_with_items(
            None, supplier_id, TODAY, TODAY, "Draft", 0, 0, 0, "", [],
        )


def test_create_with_items_persists_header_and_items():
    customer_id = _customer_id()
    supplier_id = _supplier_id()
    invoice_repository.ensure_schema()
    order_repository.ensure_schema()
    purchase_repository.ensure_schema()
    items = [_sample_item(), _sample_item(code="A2", name="Artikel 2", quantity=2, total=24.4)]

    invoice_id, invoice_number = invoice_repository.create_with_items(
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=30,
        discount=0,
        vat=6.6,
        total=36.6,
        notes="ok",
        items=items,
    )
    assert invoice_number
    assert len(invoice_repository.get_items(invoice_id)) == 2

    offer_id, offer_number = offer_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 30, 0, 6.6, 36.6, "", items,
    )
    assert offer_number.startswith("P-")
    assert len(offer_repository.get_items(offer_id)) == 2

    order_id, order_number = order_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 30, 0, 6.6, 36.6, "", items,
    )
    assert order_number.startswith("NAR-")
    assert len(order_repository.get_items(order_id)) == 2

    po_id, po_number = purchase_repository.create_with_items(
        None, supplier_id, TODAY, TODAY, "Draft", 30, 6.6, 36.6, "",
        [_po_item(), _po_item(code="P2", name="Nabava 2")],
    )
    assert po_number.startswith("PO-")
    assert len(purchase_repository.get_items(po_id)) == 2


def test_travel_order_save_validates_and_allocates_in_transaction():
    travel_order_repository.ensure_schema()
    before = len(travel_order_repository.get_all())

    with pytest.raises(ValueError, match="obvezna"):
        travel_order_repository.save(
            {
                "number": None,
                "employee": "",
                "route": "",
                "status": "Osnutek",
            }
        )
    assert len(travel_order_repository.get_all()) == before

    order_id = travel_order_repository.save(
        {
            "number": None,
            "employee": "Janez",
            "purpose": "Servis",
            "route": "LJ-KP",
            "status": "Osnutek",
            "total": 0,
            "settlement": 0,
        }
    )
    row = travel_order_repository.get_by_id(order_id)
    assert row is not None
    assert str(row[1]).startswith("PN-")
    assert row[2] == "Janez"


# --- GOLD-3B: transactional document edit ---


def _snapshot_invoice(invoice_id: int) -> tuple:
    header = invoice_repository.get_by_id(invoice_id)
    items = invoice_repository.get_items(invoice_id)
    return header, items


def test_invoice_update_with_items_persists_and_replaces():
    customer_id = _customer_id()
    invoice_repository.ensure_schema()
    invoice_id, _ = invoice_repository.create_with_items(
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=10,
        discount=0,
        vat=2.2,
        total=12.2,
        notes="before",
        items=[_sample_item()],
    )

    invoice_repository.update_with_items(
        invoice_id,
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=20,
        discount=0,
        vat=4.4,
        total=24.4,
        status="Izdan",
        notes="after",
        items=[
            _sample_item(code="B1", name="Nov", quantity=2, total=24.4),
        ],
    )
    header, items = _snapshot_invoice(invoice_id)
    assert header[10] == "after"
    assert float(header[9]) == pytest.approx(24.4)
    assert len(items) == 1
    assert items[0][2] == "B1"


def test_invoice_edit_rolls_back_on_simulated_crash(monkeypatch):
    customer_id = _customer_id()
    invoice_repository.ensure_schema()
    invoice_id, _ = invoice_repository.create_with_items(
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=10,
        discount=0,
        vat=2.2,
        total=12.2,
        notes="stable",
        items=[_sample_item(code="OLD", name="Stari")],
    )
    before = _snapshot_invoice(invoice_id)

    calls = {"n": 0}
    real_add = invoice_repository.add_item

    def boom(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated crash during edit")
        return real_add(*args, **kwargs)

    monkeypatch.setattr(invoice_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated crash during edit"):
        invoice_repository.update_with_items(
            invoice_id,
            customer_id=customer_id,
            issue_date=TODAY,
            due_date=TODAY,
            subtotal=99,
            discount=0,
            vat=0,
            total=99,
            status="Izdan",
            notes="partial",
            items=[_sample_item(code="NEW", name="Nov")],
        )

    after = _snapshot_invoice(invoice_id)
    assert after[0][10] == before[0][10] == "stable"
    assert float(after[0][9]) == pytest.approx(float(before[0][9]))
    assert [(r[2], r[3]) for r in after[1]] == [(r[2], r[3]) for r in before[1]]


def test_offer_order_purchase_edit_rolls_back_on_item_failure(monkeypatch):
    customer_id = _customer_id()
    supplier_id = _supplier_id()
    order_repository.ensure_schema()
    purchase_repository.ensure_schema()

    offer_id, _ = offer_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "o",
        [_sample_item(code="O1")],
    )
    order_id, _ = order_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "n",
        [_sample_item(code="N1")],
    )
    po_id, _ = purchase_repository.create_with_items(
        None, supplier_id, TODAY, TODAY, "Draft", 10, 2.2, 12.2, "p",
        [_po_item(code="P1")],
    )
    offer_before = offer_repository.get_items(offer_id)
    order_before = order_repository.get_items(order_id)
    po_before = purchase_repository.get_items(po_id)

    def boom(*_a, **_k):
        raise RuntimeError("simulated crash during edit")

    monkeypatch.setattr(offer_repository, "add_item", boom)
    monkeypatch.setattr(order_repository, "add_item", boom)
    monkeypatch.setattr(purchase_repository, "add_item", boom)

    with pytest.raises(RuntimeError, match="simulated crash"):
        offer_repository.update_with_items(
            offer_id, customer_id, TODAY, TODAY, "Osnutek", 50, 0, 0, 50, "x",
            [_sample_item(code="OX")],
        )
    with pytest.raises(RuntimeError, match="simulated crash"):
        order_repository.update_with_items(
            order_id, customer_id, TODAY, TODAY, "Osnutek", 50, 0, 0, 50, "x",
            [_sample_item(code="NX")],
        )
    with pytest.raises(RuntimeError, match="simulated crash"):
        purchase_repository.update_with_items(
            po_id, supplier_id, TODAY, TODAY, "Draft", 50, 0, 50, "x",
            [_po_item(code="PX")],
        )

    assert [(r[2], r[3]) for r in offer_repository.get_items(offer_id)] == [
        (r[2], r[3]) for r in offer_before
    ]
    assert [(r[2], r[3]) for r in order_repository.get_items(order_id)] == [
        (r[2], r[3]) for r in order_before
    ]
    assert [(r[2], r[3]) for r in purchase_repository.get_items(po_id)] == [
        (r[2], r[3]) for r in po_before
    ]
    assert offer_repository.get_by_id(offer_id)[10] == "o"
    assert order_repository.get_by_id(order_id)[10] == "n"
    assert purchase_repository.get_by_id(po_id)[9] == "p"


def test_nested_transaction_leaf_methods_do_not_commit_early():
    """Outer txn owns commit; leaf update/delete/add with conn must not persist alone."""
    customer_id = _customer_id()
    invoice_repository.ensure_schema()
    invoice_id, _ = invoice_repository.create_with_items(
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=10,
        discount=0,
        vat=2.2,
        total=12.2,
        notes="outer",
        items=[_sample_item(code="KEEP")],
    )
    before = _snapshot_invoice(invoice_id)
    vat_liable = invoice_repository.get_vat_liable(invoice_id)

    with pytest.raises(RuntimeError, match="simulated outer crash"):
        with db.transaction(immediate=True) as conn:
            invoice_repository.update(
                invoice_id=invoice_id,
                customer_id=customer_id,
                issue_date=TODAY,
                due_date=TODAY,
                subtotal=77,
                discount=0,
                vat=0,
                total=77,
                status="Izdan",
                notes="nested-dirty",
                vat_liable=vat_liable,
                conn=conn,
            )
            invoice_repository.delete_items(invoice_id, conn=conn)
            # Uncommitted deletes must not be visible on an independent connection.
            peek = sqlite3.connect(str(db.database))
            try:
                count = peek.execute(
                    "SELECT COUNT(*) FROM invoice_items WHERE invoice_id=?",
                    (invoice_id,),
                ).fetchone()[0]
                assert int(count) == len(before[1])
            finally:
                peek.close()
            invoice_repository.add_item(
                invoice_id=invoice_id,
                article_id=None,
                code="TEMP",
                name="Temp",
                description="",
                quantity=1,
                unit="kos",
                price=1,
                discount=0,
                vat=0,
                total=1,
                conn=conn,
            )
            raise RuntimeError("simulated outer crash")

    after = _snapshot_invoice(invoice_id)
    assert after[0][10] == "outer"
    assert float(after[0][9]) == pytest.approx(12.2)
    assert [(r[2], r[3]) for r in after[1]] == [(r[2], r[3]) for r in before[1]]


def test_update_with_items_rejects_empty_items():
    customer_id = _customer_id()
    supplier_id = _supplier_id()
    invoice_repository.ensure_schema()
    order_repository.ensure_schema()
    purchase_repository.ensure_schema()

    invoice_id, _ = invoice_repository.create_with_items(
        customer_id=customer_id,
        issue_date=TODAY,
        due_date=TODAY,
        subtotal=10,
        discount=0,
        vat=2.2,
        total=12.2,
        notes="",
        items=[_sample_item()],
    )
    offer_id, _ = offer_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
        [_sample_item()],
    )
    order_id, _ = order_repository.create_with_items(
        None, customer_id, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
        [_sample_item()],
    )
    po_id, _ = purchase_repository.create_with_items(
        None, supplier_id, TODAY, TODAY, "Draft", 10, 2.2, 12.2, "",
        [_po_item()],
    )

    with pytest.raises(ValueError, match="postavko"):
        invoice_repository.update_with_items(
            invoice_id,
            customer_id=customer_id,
            issue_date=TODAY,
            due_date=TODAY,
            subtotal=0,
            discount=0,
            vat=0,
            total=0,
            status="Izdan",
            notes="",
            items=[],
        )
    with pytest.raises(ValueError, match="postavko"):
        offer_repository.update_with_items(
            offer_id, customer_id, TODAY, TODAY, "Osnutek", 0, 0, 0, 0, "", [],
        )
    with pytest.raises(ValueError, match="postavko"):
        order_repository.update_with_items(
            order_id, customer_id, TODAY, TODAY, "Osnutek", 0, 0, 0, 0, "", [],
        )
    with pytest.raises(ValueError, match="postavko"):
        purchase_repository.update_with_items(
            po_id, supplier_id, TODAY, TODAY, "Draft", 0, 0, 0, "", [],
        )
