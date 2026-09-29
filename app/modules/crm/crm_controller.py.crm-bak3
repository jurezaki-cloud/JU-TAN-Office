from __future__ import annotations

from html import escape
from pathlib import Path

from app.excel.excel_export import excel_folders, write_workbook
from app.modules.crm.crm_repository import DEAL_STATUSES, crm_repository
from app.modules.crm.crm_service import crm_service


class CrmController:
    def __init__(self, service=crm_service, repository=crm_repository) -> None:
        self.service = service
        self.repository = repository

    def kpis(self) -> dict:
        return self.service.kpis()

    def deals(self, **filters) -> list:
        return self.service.filter_deals(**filters)

    def search_customers(self, query: str) -> list:
        return self.service.search_customers(query)

    def customer_360(self, customer_id: int) -> dict:
        return self.service.customer_360(customer_id)

    def followups(self) -> dict:
        return self.service.followups()

    def create_lead(self, data: dict) -> int:
        return self.service.create_lead(data)

    def add_activity(self, data: dict) -> int:
        return self.service.add_activity(data)

    def set_stage(self, deal_id: int, stage: str) -> None:
        self.service.set_stage(deal_id, stage)

    def salespeople(self) -> list[str]:
        owner = self.service.default_owner()
        people = list(self.repository.salespeople())
        if owner and owner not in people:
            people.insert(0, owner)
        return people

    def stages(self) -> tuple[str, ...]:
        return self.service.stages()

    def statuses(self) -> tuple[str, ...]:
        return DEAL_STATUSES

    def export_excel(self, path: Path, deals: list) -> Path:
        headers = ["Naslov", "Podjetje", "Stage", "Status", "Prioriteta", "Skrbnik", "Vrednost"]
        rows = [
            [row[3], row[4], row[5], row[9], row[7], row[6], row[8]]
            for row in deals
        ]
        return write_workbook(path, "crm", headers, rows)

    def export_start_path(self) -> Path:
        return excel_folders()["export"] / "crm.xlsx"

    def print_html(self, deals: list) -> str:
        from app.core.permissions import audit, require

        require("print")
        audit("print", "crm")
        rows = "".join(
            "<tr>"
            f"<td>{escape(str(row[3] or ''))}</td>"
            f"<td>{escape(str(row[4] or ''))}</td>"
            f"<td>{escape(str(row[5] or ''))}</td>"
            f"<td>{escape(str(row[9] or ''))}</td>"
            f"<td>{row[8]}</td>"
            "</tr>"
            for row in deals
        )
        return (
            "<h2>CRM Pipeline</h2>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>Naslov</th><th>Podjetje</th><th>Stage</th>"
            "<th>Status</th><th>Vrednost</th></tr>"
            f"{rows}</table>"
        )
