from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.core.constants import DATA_DIR
from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.modules.documents.documents_repository import (
    FILE_KINDS,
    LINK_MODULES,
    documents_repository,
)
from app.modules.purchase.purchase_repository import purchase_repository
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import warehouse_service
from app.pdf.pdf_company import load_company

DOCUMENTS_DIR = DATA_DIR / "documents"

ALLOWED_EXT = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".zip": "zip",
    ".txt": "txt",
}


class DocumentsService:
    def __init__(self, root: Path | None = None, repository=documents_repository) -> None:
        self.root = root or DOCUMENTS_DIR
        self.repository = repository
        self.root.mkdir(parents=True, exist_ok=True)

    def default_owner(self) -> str:
        return (load_company().name or "JU-TAN").strip()

    def link_modules(self) -> tuple[tuple[str, str], ...]:
        return LINK_MODULES

    def link_targets(self, module: str) -> list[tuple[int | str, str]]:
        try:
            if module == "customer":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in customer_repository.get_all()]
            if module == "supplier":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in suppliers_repository.get_all()]
            if module == "invoice":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in invoice_repository.get_all()]
            if module == "offer":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in offer_repository.get_all()]
            if module == "order":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in order_repository.get_all()]
            if module == "purchase":
                return [(row[0], str(row[1] or f"#{row[0]}")) for row in purchase_repository.get_all()]
            if module == "product":
                return [
                    (row[0], " — ".join(p for p in (str(row[1] or ""), str(row[2] or "")) if p))
                    for row in article_repository.get_all()
                ]
            if module == "warehouse":
                items = []
                for movement in warehouse_service.movements():
                    label = " · ".join(
                        part for part in (
                            str(movement.get("type") or ""),
                            str(movement.get("article_name") or ""),
                            str(movement.get("date") or "")[:10],
                        ) if part
                    )
                    items.append((movement.get("id"), label or f"#{movement.get('id')}"))
                return items
            if module == "crm":
                return []
        except Exception:
            return []
        return []

    def upload(
        self,
        source: Path,
        parent_id: int | None,
        owner: str,
        module: str = "",
        entity_id=None,
        entity_label: str = "",
        name: str | None = None,
    ) -> int:
        source = Path(source)
        ext = source.suffix.lower()
        if ext not in ALLOWED_EXT:
            raise ValueError("Nepodprta datoteka. Dovoljeni: PDF, DOCX, XLSX, PNG, JPG, ZIP, TXT.")
        from app.core.permissions import audit, require
        from app.core.security import ensure_inside, safe_filename

        require("write")
        kind = ALLOWED_EXT[ext]
        stored = f"{uuid.uuid4().hex}{ext}"
        target = ensure_inside(self.root / stored, self.root)
        shutil.copy2(source, target)
        display = safe_filename(name or source.name)
        doc_id = self.repository.add(
            parent_id=parent_id,
            name=display,
            is_folder=False,
            stored_name=stored,
            original_name=source.name,
            extension=ext.lstrip("."),
            kind=kind,
            size_bytes=target.stat().st_size,
            owner=owner or self.default_owner(),
            module=module or "",
            entity_id=entity_id,
            entity_label=entity_label or "",
        )
        audit("create", f"document:{display}")
        return doc_id

    def create_folder(self, name: str, parent_id: int | None, owner: str) -> int:
        title = name.strip()
        if not title:
            raise ValueError("Ime mape je obvezno.")
        return self.repository.add(
            parent_id=parent_id,
            name=title,
            is_folder=True,
            kind="folder",
            owner=owner or self.default_owner(),
        )

    def rename(self, document_id: int, name: str) -> None:
        title = name.strip()
        if not title:
            raise ValueError("Ime je obvezno.")
        self.repository.update_meta(document_id, name=title)

    def move(self, document_id: int, parent_id: int | None) -> None:
        if parent_id == document_id:
            raise ValueError("Mape ni mogoče premakniti vase.")
        if parent_id is not None:
            for child in self.repository.descendants(document_id):
                if child[0] == parent_id:
                    raise ValueError("Mape ni mogoče premakniti v podmapo.")
        self.repository.update_meta(document_id, parent_id=parent_id)

    def copy(self, document_id: int, parent_id: int | None) -> int:
        row = self.repository.get(document_id)
        if row is None:
            raise ValueError("Dokument ne obstaja.")
        if row[3]:
            new_id = self.repository.add(
                parent_id=parent_id,
                name=f"{row[2]} (kopija)",
                is_folder=True,
                kind="folder",
                owner=row[9],
            )
            for child in self.repository.children(document_id):
                self.copy(child[0], new_id)
            return new_id
        source = self.path_for(row)
        ext = f".{row[6]}" if row[6] else ""
        stored = f"{uuid.uuid4().hex}{ext}"
        target = self.root / stored
        if source.exists():
            shutil.copy2(source, target)
            size = target.stat().st_size
        else:
            size = int(row[8] or 0)
        return self.repository.add(
            parent_id=parent_id,
            name=f"{row[2]} (kopija)",
            is_folder=False,
            stored_name=stored,
            original_name=row[5],
            extension=row[6],
            kind=row[7],
            size_bytes=size,
            owner=row[9],
            module=row[10],
            entity_id=row[11],
            entity_label=row[12],
        )

    def delete(self, document_id: int) -> None:
        row = self.repository.get(document_id)
        if row is None:
            return
        if row[3]:
            for child in list(self.repository.children(document_id)):
                self.delete(child[0])
        else:
            path = self.path_for(row)
            if path.exists():
                path.unlink()
        self.repository.delete(document_id)

    def download(self, document_id: int, target: Path) -> Path:
        row = self.repository.get(document_id)
        if row is None or row[3]:
            raise ValueError("Izberi datoteko.")
        source = self.path_for(row)
        if not source.exists():
            raise ValueError("Datoteka ni na disku.")
        target = Path(target)
        shutil.copy2(source, target)
        return target

    def path_for(self, row) -> Path:
        from app.core.security import ensure_inside

        name = Path(str(row[4] or "")).name
        return ensure_inside(self.root / name, self.root)

    def file_kinds(self) -> tuple[str, ...]:
        return FILE_KINDS


documents_service = DocumentsService()
