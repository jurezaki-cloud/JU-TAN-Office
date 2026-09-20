"""Controller za Automation Engine."""

from __future__ import annotations

from pathlib import Path

from app.excel.excel_export import excel_folders, write_workbook
from app.modules.automation.automation_repository import ACTION_LABELS, TRIGGER_LABELS
from app.modules.automation.automation_service import automation_service


class AutomationController:
    def __init__(self, service=automation_service) -> None:
        self.service = service

    def kpis(self) -> dict:
        return self.service.kpis()

    def rules(self, **filters) -> list:
        return self.service.rules(**filters)

    def logs(self, **filters) -> list:
        return self.service.logs(**filters)

    def get(self, rule_id: int) -> dict | None:
        return self.service.get(rule_id)

    def save(self, data: dict) -> int:
        return self.service.save(data)

    def delete(self, rule_id: int) -> None:
        self.service.delete(rule_id)

    def duplicate(self, rule_id: int) -> int:
        return self.service.duplicate(rule_id)

    def set_enabled(self, rule_id: int, enabled: bool) -> None:
        self.service.set_enabled(rule_id, enabled)

    def run_now(self, rule_id: int, context: dict | None = None) -> dict:
        return self.service.run_now(rule_id, context)

    def tick(self) -> list[dict]:
        return self.service.tick()

    def trigger_label(self, key: str) -> str:
        return TRIGGER_LABELS.get(key, key)

    def action_label(self, key: str) -> str:
        return ACTION_LABELS.get(key, key)

    def export_path(self) -> Path:
        return excel_folders()["export"] / "automation.xlsx"

    def export_excel(self, path: Path, rows: list) -> Path:
        headers = ["ID", "Ime", "Sprožilec", "Aktivno", "Prioriteta", "Razpored"]
        data = [
            [row[0], row[1], self.trigger_label(row[2]), "Da" if row[3] else "Ne", row[4], row[5]]
            for row in rows
        ]
        return write_workbook(path, "automation", headers, data)


automation_controller = AutomationController()
