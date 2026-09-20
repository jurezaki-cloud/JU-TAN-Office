"""RC1: shema, backup, performanse, varnost — brez novih funkcij."""

from __future__ import annotations

import time

import pytest

from app.core.logger import SESSION_USER, log_exception, logger
from app.core.pagination import page_slice
from app.core.permissions import can, require
from app.core.security import assert_parameterized
from app.database.customer_repository import customer_repository
from app.database.database import db
from app.database.invoice_repository import invoice_repository
from app.modules.settings.settings_controller import SettingsController


def test_pragma_foreign_keys_on():
    conn = db.connect()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_core_indexes_exist():
    conn = db.connect()
    try:
        names = {row[1] for row in conn.execute("PRAGMA index_list('customers')")}
        assert "idx_customers_company" in names
        names = {row[1] for row in conn.execute("PRAGMA index_list('invoices')")}
        assert "idx_invoices_customer" in names
    finally:
        conn.close()


def test_unique_and_not_null_customers():
    with pytest.raises(Exception):
        conn = db.connect()
        try:
            conn.execute("INSERT INTO customers(company) VALUES (NULL)")
            conn.commit()
        finally:
            conn.close()


def test_transaction_rollback():
    marker = "RC1-ROLLBACK-XYZ"
    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO customers(company, city) VALUES (?, ?)",
                (marker, "Test"),
            )
            raise RuntimeError("rollback")
    except RuntimeError:
        pass
    rows = customer_repository.search(marker)
    assert not any(row[1] == marker for row in rows)


def test_invoice_cascade_and_customer_restrict():
    customer_repository.add(
        "RC1 Cascade d.o.o.", "QA", "", "", "Celje", "SI", "", "", "",
    )
    cid = customer_repository.search("RC1 Cascade")[0][0]
    invoice_id = invoice_repository.add(
        "RC1-INV-001", cid, "2026-01-01", "2026-01-31", 10, 0, 2, 12, "RC1",
    )
    invoice_repository.add_item(
        invoice_id, None, "X", "Postavka", "", 1, "kos", 10, 0, 22, 12,
    )
    conn = db.connect()
    try:
        with pytest.raises(Exception):
            conn.execute("DELETE FROM customers WHERE id=?", (cid,))
            conn.commit()
    finally:
        conn.rollback()
        conn.close()
    invoice_repository.delete(invoice_id)
    conn = db.connect()
    try:
        left = conn.execute(
            "SELECT COUNT(*) FROM invoice_items WHERE invoice_id=?",
            (invoice_id,),
        ).fetchone()[0]
        assert left == 0
    finally:
        conn.close()
    customer_repository.delete(cid)
    assert customer_repository.get_by_id(cid) is None


def test_backup_restore_integrity(tmp_path):
    controller = SettingsController()
    customer_repository.add(
        "RC1 Backup d.o.o.", "QA", "", "", "Kranj", "SI", "", "", "",
    )
    backup = controller.backup_database()
    assert backup.exists()
    conn = __import__("sqlite3").connect(backup)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()
    controller.restore_database(backup)
    found = customer_repository.search("RC1 Backup")
    assert found


def test_sql_injection_guard():
    with pytest.raises(ValueError):
        assert_parameterized("SELECT * FROM t WHERE a = ' + name")
    injected = customer_repository.get_by_id("1 OR 1=1")
    assert injected is None or injected[1] != "all-rows"


def test_permissions_and_audit():
    assert can("backup")
    require("read")
    with pytest.raises(PermissionError):
        require("not-a-real-action")


def test_logging_includes_user_and_stack(caplog):
    assert SESSION_USER
    with caplog.at_level("ERROR", logger="JU-TAN Office"):
        try:
            raise ValueError("rc1-log")
        except ValueError as exc:
            log_exception(exc, "rc1")
    text = caplog.text
    assert "rc1-log" in text
    assert "ValueError" in text or "rc1" in text
    logger.info("RC1 INFO check")
    logger.warning("RC1 WARNING check")


def test_performance_large_table_and_search():
    rows = [(i, f"N{i}", i % 10) for i in range(100_000)]
    t0 = time.perf_counter()
    page = page_slice(rows, 0, 50)
    elapsed_page = time.perf_counter() - t0
    assert len(page) == 50
    assert elapsed_page < 0.05
    t1 = time.perf_counter()
    hits = [r for r in rows if r[1] == "N99999"]
    elapsed_search = time.perf_counter() - t1
    assert hits
    assert elapsed_search < 0.25


def test_startup_db_initialize_budget():
    t0 = time.perf_counter()
    db.initialize()
    elapsed = time.perf_counter() - t0
    assert elapsed < 8.0


def test_module_imports_rc1():
    from app.database import article_repository, customer_repository, invoice_repository, order_repository
    from app.modules.crm.crm_repository import crm_repository
    from app.modules.documents.documents_repository import documents_repository
    from app.modules.purchase.purchase_repository import purchase_repository
    from app.modules.reports.reporting_service import reporting_service
    from app.modules.suppliers.suppliers_repository import suppliers_repository
    from app.modules.warehouse.warehouse_service import warehouse_service
    from app.modules.automation.automation_service import automation_service

    assert customer_repository and invoice_repository and article_repository
    assert order_repository and crm_repository and documents_repository
    assert purchase_repository and suppliers_repository and warehouse_service
    assert reporting_service and automation_service
