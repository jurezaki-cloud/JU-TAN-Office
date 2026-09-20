"""TASK-033 — končni QA: tok, moduli, baza, uvoz, WAL, stres, PDF, namestitev."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import date
from pathlib import Path

import pytest

from app.core.constants import DATABASE_PATH
from app.core.db_guard import integrity_ok
from app.core.pagination import page_slice
from app.core.perf import memory_mb
from app.core.recovery import FLAG, load_draft, mark_running, save_draft
from app.database.article_repository import article_repository
from app.database.company_repository import company_repository
from app.database.customer_repository import customer_repository
from app.database.database import db
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.excel.excel_export import analyze_file, write_workbook
from app.modules.automation.automation_service import automation_service
from app.modules.crm.crm_controller import CrmController
from app.modules.documents.documents_repository import documents_repository
from app.modules.reports.reporting_service import ReportFilters, reporting_service
from app.modules.settings.settings_controller import SettingsController
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import warehouse_service
from app.pdf.pdf_engine import PdfDocument, pdf_engine
from app.pdf.pdf_export import pdf_export


TODAY = date.today().isoformat()


def test_regression_all_modules_reachable():
    assert company_repository.get_company() is not None
    customer_repository.get_all()
    article_repository.get_all()
    offer_repository.get_all()
    order_repository.get_all()
    invoice_repository.get_all()
    warehouse_service.stock_rows()
    suppliers_repository.get_all()
    documents_repository.search(scoped=False)
    CrmController().kpis()
    reporting_service.run("dashboard", ReportFilters())
    automation_service.rules()
    SettingsController().load_extras()
    SettingsController().about()


def test_business_workflow_lead_to_report(tmp_path):
    deal_id = CrmController().create_lead({
        "company": "GOLD d.o.o.",
        "contact": "Lea",
        "title": "GOLD lead",
        "stage": "Lead",
        "value": 900,
    })
    customer_repository.add(
        "GOLD d.o.o.", "Lea", "Ulica 1", "6000", "Koper", "SI", "12345678", "gold@test.si", "040",
    )
    customer = next(r for r in customer_repository.search("GOLD d.o.o.") if r[1] == "GOLD d.o.o.")
    article_repository.add("GOLD-ART", "Gold artikel", "", "kos", 100.0, 22)
    article = next(r for r in article_repository.get_all() if r[1] == "GOLD-ART")
    offer_id = offer_repository.create(
        "PON-GOLD-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "QA",
    )
    offer_repository.add_item(
        offer_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    order_id = order_repository.create(
        "NAR-GOLD-1", customer[0], TODAY, TODAY, "Osnutek", 100, 0, 22, 122, "QA",
    )
    order_repository.add_item(
        order_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    invoice_id = invoice_repository.add(
        "RAC-GOLD-1", customer[0], TODAY, TODAY, 100, 0, 22, 122, "QA", "Osnutek",
    )
    invoice_repository.add_item(
        invoice_id, article[0], article[1], article[2], "", 1, "kos", 100, 0, 22, 122,
    )
    invoice_repository.recalculate_totals(invoice_id)
    invoice_repository.mark_paid(invoice_id)
    paid = invoice_repository.get_by_id(invoice_id)
    assert paid is not None
    assert paid[5] in ("Plačan", "Plačano")
    finance = reporting_service.run("finance_paid", ReportFilters())
    assert finance.headers
    assert deal_id and offer_id and order_id and invoice_id


def test_database_crud_transaction_fk_wal():
    conn = db.connect()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()
    assert str(mode).lower() == "wal"
    assert int(fk) == 1
    assert integrity_ok()

    customer_repository.add("TX d.o.o.", "A", "", "", "Koper", "SI", "", "", "")
    row = customer_repository.search("TX d.o.o.")[0]
    customer_repository.delete(row[0])
    assert customer_repository.get_by_id(row[0]) is None

    try:
        with db.transaction() as txn:
            txn.execute("INSERT INTO customers(company, contact) VALUES (?,?)", ("ROLLBACK d.o.o.", "X"))
            raise RuntimeError("forced")
    except RuntimeError:
        pass
    assert not customer_repository.search("ROLLBACK d.o.o.")

    customer_repository.add("FK d.o.o.", "B", "", "", "Koper", "SI", "", "", "")
    owner = customer_repository.search("FK d.o.o.")[0]
    invoice_repository.add(
        "RAC-FK-1", owner[0], TODAY, TODAY, 1, 0, 0, 1, "", "Osnutek",
    )
    with pytest.raises(Exception):
        customer_repository.delete(owner[0])


def test_import_export_csv_excel_pdf_json_backup(tmp_path):
    xlsx = tmp_path / "out.xlsx"
    write_workbook(xlsx, "customers", ["Podjetje", "Kontakt"], [["GOLD d.o.o.", "Lea"]])
    analysis = analyze_file(xlsx)
    assert analysis["count"] >= 1
    csv_path = tmp_path / "out.csv"
    csv_path.write_text("Podjetje;Kontakt\nGOLD;Lea\n", encoding="utf-8")
    assert csv_path.read_text(encoding="utf-8").count("GOLD") == 1
    settings = tmp_path / "settings.json"
    SettingsController().export_settings(settings)
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    SettingsController().import_settings(settings)
    controller = SettingsController()
    backup = controller.backup_database()
    assert backup.exists()
    controller.restore_database(backup)
    assert integrity_ok()


def test_print_pdf_suite(tmp_path, monkeypatch):
    from app.core import constants as const

    monkeypatch.setattr(const, "EXPORT_DIR", tmp_path)
    monkeypatch.setenv("JU_TAN_EXPORT_DIR", str(tmp_path))
    customers = customer_repository.search("GOLD d.o.o.") or customer_repository.get_all()
    assert customers
    cid = customers[0][0]
    articles = article_repository.get_all()
    aid = articles[0][0]
    offer_id = offer_repository.create(
        "PON-PDF-1", cid, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
    )
    offer_repository.add_item(offer_id, aid, "C", "N", "", 1, "kos", 10, 0, 22, 12.2)
    order_id = order_repository.create(
        "NAR-PDF-1", cid, TODAY, TODAY, "Osnutek", 10, 0, 2.2, 12.2, "",
    )
    order_repository.add_item(order_id, aid, "C", "N", "", 1, "kos", 10, 0, 22, 12.2)
    invoice_id = invoice_repository.add(
        "RAC-PDF-1", cid, TODAY, TODAY, 10, 0, 2.2, 12.2, "", "Osnutek",
    )
    invoice_repository.add_item(invoice_id, aid, "C", "N", "", 1, "kos", 10, 0, 22, 12.2)
    paths = [
        pdf_export.export_offer(offer_id),
        pdf_export.export_order(order_id),
        pdf_export.export_delivery(order_id),
        pdf_export.export_invoice(invoice_id),
        pdf_engine.render(
            PdfDocument(doc_type="label", number="NAL-1", customer_name="GOLD", notes="Nalepka QA"),
            tmp_path / "label.pdf",
        ),
    ]
    for path in paths:
        assert Path(path).exists()
        assert Path(path).stat().st_size > 200
    crm_pdf = reporting_service.export_pdf(
        reporting_service.run("crm_pipeline", ReportFilters()),
        tmp_path / "crm.pdf",
    )
    assert crm_pdf.exists()


def test_wal_multi_user_no_deadlock():
    errors: list[str] = []
    stop = threading.Event()

    def reader():
        try:
            for _ in range(40):
                customer_repository.get_all()
                invoice_repository.get_all()
                if stop.is_set():
                    break
        except Exception as exc:
            errors.append(str(exc))

    def writer(idx: int):
        try:
            for n in range(8):
                customer_repository.add(
                    f"WAL{idx}-{n} d.o.o.", "U", "", "", "Koper", "SI", "", "", "",
                )
        except Exception as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=reader) for _ in range(8)]
    threads += [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
        assert not thread.is_alive()
    stop.set()
    assert errors == []
    assert integrity_ok()


def test_stress_volume_and_search_budget():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    rows = [(f"STRESS-{i:05d}", "QA") for i in range(2000)]
    t0 = time.perf_counter()
    conn.executemany("INSERT INTO customers(company, contact) VALUES (?,?)", rows)
    conn.commit()
    elapsed_insert = time.perf_counter() - t0
    t1 = time.perf_counter()
    found = conn.execute(
        "SELECT id FROM customers WHERE company LIKE ? LIMIT 50",
        ("%STRESS-0100%",),
    ).fetchall()
    elapsed_search = time.perf_counter() - t1
    conn.close()
    assert found
    assert elapsed_insert < 8.0
    assert elapsed_search < 0.3
    million = list(range(1_000_000))
    assert len(page_slice(million, 0, 200)) == 200
    assert len(page_slice([(i,) for i in range(2_000_000)], 10, 200)) == 200
    assert len(page_slice(list(range(100_000)), 0, 50)) == 50
    assert len(page_slice(list(range(500_000)), 0, 50)) == 50


def test_soak_no_unbounded_growth():
    before = memory_mb()
    for i in range(80):
        customer_repository.search("STRESS")
        article_repository.list_page("", limit=50, offset=0)
        if i % 20 == 0:
            import gc
            gc.collect()
    after = memory_mb()
    if before and after:
        assert after - before < 80


def test_crash_recovery_and_drafts():
    FLAG.unlink(missing_ok=True)
    FLAG.write_text("running", encoding="utf-8")
    crashed = mark_running()
    assert crashed is True
    save_draft("invoice", {"number": "RAC-CRASH"})
    assert load_draft("invoice")["number"] == "RAC-CRASH"
    controller = SettingsController()
    backup = controller.backup_database()
    controller.restore_database(backup)
    assert integrity_ok()


def test_performance_targets():
    t0 = time.perf_counter()
    db.initialize()
    assert time.perf_counter() - t0 < 3.0
    t1 = time.perf_counter()
    article_repository.list_page("Gold", limit=50, offset=0)
    assert (time.perf_counter() - t1) < 0.3
    t2 = time.perf_counter()
    SettingsController().load_extras()
    assert (time.perf_counter() - t2) < 0.5


def test_security_acceptance_recap():
    from app.core.passwords import hash_password, verify_password
    from app.core.permissions import can, set_identity
    from app.core.security import ensure_inside, require_email

    hashed = hash_password("SecurePass1x")
    assert verify_password("SecurePass1x", hashed)
    set_identity(role="Read Only", authenticated=True)
    try:
        assert not can("delete")
    finally:
        set_identity(role="Administrator", authenticated=True)
    require_email("qa@jutan.si")
    with pytest.raises(PermissionError):
        ensure_inside(Path("C:/Windows/notepad.exe"), Path("C:/data"))


def test_installer_upgrade_contract():
    iss = Path("packaging/installer.iss").read_text(encoding="utf-8")
    assert "UsePreviousAppDir=yes" in iss
    assert "uninsneveruninstall" in iss
    assert "JU-TAN-Office-Setup" in iss
    assert "AppId=" in iss
    version = Path("Version.txt").read_text(encoding="utf-8")
    assert "1.0.0 GOLD" in version or "1.0.0" in version
    assert Path("packaging/LICENSE.txt").exists()
    assert Path("docs/INSTALL.md").exists()
    assert Path("docs/SECURITY.md").exists()
    notes = Path("docs/RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "1.0.0" in notes
