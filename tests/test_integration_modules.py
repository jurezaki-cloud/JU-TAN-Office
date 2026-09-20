"""Integracijski testi: CRM, DMS, Inventory, Purchase, Reports."""

from datetime import date
from pathlib import Path

from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.excel.excel_export import write_workbook
from app.modules.crm.crm_controller import CrmController
from app.modules.crm.crm_repository import crm_repository
from app.modules.documents.documents_repository import documents_repository
from app.modules.purchase.purchase_repository import purchase_repository
from app.modules.reports.reporting_service import ReportFilters, reporting_service
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import WarehouseService, warehouse_service


def test_crm_lead_pipeline_and_activity():
    controller = CrmController()
    deal_id = controller.create_lead({
        "company": "CRM Test d.o.o.",
        "contact": "Bojan",
        "title": "Nov lead",
        "stage": "Lead",
        "value": 1500,
    })
    assert deal_id
    controller.set_stage(deal_id, "Qualified")
    deal = crm_repository.get_deal(deal_id)
    assert deal is not None
    activity_id = controller.add_activity({
        "pipeline_id": deal_id,
        "type": "Call",
        "title": "Klic",
    })
    assert activity_id
    assert controller.kpis()["active"] >= 1
    assert controller.deals()


def test_dms_folder_search_and_delete():
    folder_id = documents_repository.add(name="Mapa T025", is_folder=True, owner="QA")
    file_id = documents_repository.add(
        name="pogodba.txt",
        parent_id=folder_id,
        is_folder=False,
        kind="txt",
        extension="txt",
        owner="QA",
        module="customer",
    )
    kids = documents_repository.children(folder_id)
    assert any(row[0] == file_id for row in kids)
    found = documents_repository.search("pogodba", scoped=False)
    assert found
    documents_repository.delete(file_id)
    documents_repository.delete(folder_id)
    assert documents_repository.get(folder_id) is None


def test_inventory_movement(tmp_path):
    if not any(row[1] == "WH-T025" for row in article_repository.get_all()):
        article_repository.add("WH-T025", "Zaloga test", "", "kos", 5.0, 22)
    article = next(row for row in article_repository.get_all() if row[1] == "WH-T025")
    service = WarehouseService(path=tmp_path / "warehouse.json")
    service.add_movement(
        movement_type="Prevzem",
        article_id=article[0],
        warehouse_id="main",
        quantity=10,
        user="QA",
        note="test",
    )
    rows = service.stock_rows()
    match = next(r for r in rows if r.article_id == article[0])
    assert match.qty >= 10


def test_purchase_order_flow():
    supplier_id = suppliers_repository.add(
        "Dobavitelj T025", "", "Kontakt", "", "", "Active", ""
    )
    purchase_id = purchase_repository.create(
        "PO-T025",
        supplier_id,
        date.today().isoformat(),
        date.today().isoformat(),
        "Draft",
        10.0,
        2.2,
        12.2,
        "",
    )
    article_repository.add("PO-ART-T025", "Nabava artikel", "", "kos", 10.0, 22)
    article = next(r for r in article_repository.get_all() if r[1] == "PO-ART-T025")
    purchase_repository.add_item(
        purchase_id, article[0], article[1], article[2], 2, 0, 10.0, 22, 20.0
    )
    rows = purchase_repository.get_all()
    assert any(row[0] == purchase_id for row in rows)
    found = purchase_repository.search("PO-T025")
    assert found


def test_reports_dashboard_and_excel(tmp_path):
    result = reporting_service.run("dashboard", ReportFilters())
    assert result.headers
    options = reporting_service.filter_options()
    assert "customers" in options
    again = reporting_service.filter_options()
    assert again == options
    path = tmp_path / "report.xlsx"
    reporting_service.export_excel(result, path)
    assert path.exists()
    csv_path = tmp_path / "report.csv"
    reporting_service.export_csv(result, csv_path)
    assert csv_path.exists()


def test_automation_module_present():
    from app.modules.automation import AutomationPage
    assert AutomationPage is not None
