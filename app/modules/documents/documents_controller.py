from __future__ import annotations

from datetime import date
from pathlib import Path

from app.excel.excel_export import excel_folders, write_workbook
from app.modules.documents.documents_repository import documents_repository
from app.modules.documents.documents_service import documents_service


class DocumentsController:
    def __init__(self, service=documents_service, repository=documents_repository) -> None:
        self.service = service
        self.repository = repository
        self.folder_id: int | None = None

    def kpis(self) -> dict:
        return self.repository.kpis()

    def list_rows(
        self,
        query: str = "",
        kind: str = "all",
        module: str = "all",
        owner: str = "all",
        date_filter: str = "all",
        selected_date: str | None = None,
    ) -> list:
        date_from = date_to = None
        today = date.today()
        if date_filter == "today":
            date_from = f"{today.isoformat()}T00:00:00"
            date_to = f"{today.isoformat()}T23:59:59"
        elif date_filter == "month":
            date_from = f"{today.strftime('%Y-%m')}-01T00:00:00"
        elif date_filter == "day" and selected_date:
            date_from = f"{selected_date}T00:00:00"
            date_to = f"{selected_date}T23:59:59"
        scoped = not (
            query.strip()
            or kind not in ("all", "", None)
            or module not in ("all", "", None)
            or owner not in ("all", "", None)
            or date_filter not in ("all", "", None)
        )
        return self.repository.search(
            query=query,
            kind=kind,
            module=module,
            owner=owner,
            date_from=date_from,
            date_to=date_to,
            parent_id=self.folder_id,
            scoped=scoped,
        )

    def breadcrumb(self) -> str:
        names = []
        current = self.folder_id
        while current is not None:
            row = self.repository.get(current)
            if row is None:
                break
            names.append(row[2])
            current = row[1]
        names.reverse()
        return " / ".join(["Dokumenti"] + names)

    def enter_folder(self, folder_id: int | None) -> None:
        self.folder_id = folder_id

    def go_up(self) -> None:
        if self.folder_id is None:
            return
        row = self.repository.get(self.folder_id)
        self.folder_id = None if row is None else row[1]

    def owners(self) -> list[str]:
        return self.repository.owners()

    def folders(self) -> list:
        return self.repository.folders()

    def upload(self, path: Path, **meta) -> int:
        return self.service.upload(path, self.folder_id, **meta)

    def new_folder(self, name: str, owner: str) -> int:
        return self.service.create_folder(name, self.folder_id, owner)

    def rename(self, document_id: int, name: str) -> None:
        self.service.rename(document_id, name)

    def move(self, document_id: int, parent_id: int | None) -> None:
        self.service.move(document_id, parent_id)

    def copy(self, document_id: int, parent_id: int | None) -> int:
        return self.service.copy(document_id, parent_id)

    def delete(self, document_id: int) -> None:
        self.service.delete(document_id)

    def download(self, document_id: int, target: Path) -> Path:
        return self.service.download(document_id, target)

    def path_for_id(self, document_id: int) -> Path | None:
        row = self.repository.get(document_id)
        if row is None or row[3]:
            return None
        return self.service.path_for(row)

    def get(self, document_id: int):
        return self.repository.get(document_id)

    def export_excel(self, path: Path, rows: list) -> Path:
        headers = ["Ime", "Tip", "Velikost", "Datum", "Povezano z", "Lastnik"]
        data = []
        for row in rows:
            data.append([
                row[2],
                "Mapa" if row[3] else (row[7] or "").upper(),
                row[8],
                str(row[13] or "")[:19],
                _linked(row),
                row[9] or "",
            ])
        return write_workbook(path, "documents", headers, data)

    def export_start_path(self) -> Path:
        return excel_folders()["export"] / "documents.xlsx"


def _linked(row) -> str:
    module = str(row[10] or "").strip()
    label = str(row[12] or "").strip()
    if module and label:
        return f"{module}: {label}"
    return module or label or "—"
