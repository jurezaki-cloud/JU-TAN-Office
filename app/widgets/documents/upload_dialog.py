from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.modules.documents.documents_service import documents_service
from app.widgets.cards.enterprise_card import EnterpriseCard


class UploadDialog(EnterpriseDialog):

    def __init__(self, parent=None, service=documents_service) -> None:
        super().__init__(
            parent,
            title="Upload",
            heading="Naloži dokument",
            size="SMALL",
            state_key="dialog.upload",
            save_text="Upload",
        )
        self.service = service
        self.paths: list[Path] = []
        self.setObjectName("UploadDialog")
        self.setAcceptDrops(True)
        self.bind_save(self._accept)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.drop = QLabel("Povleci datoteke sem\nali izberi z gumbom")
        self.drop.setObjectName("EmptyStateSubtitle")
        self.drop.setAlignment(Qt.AlignCenter)
        self.drop.setMinimumHeight(88)
        self.drop.setAcceptDrops(True)
        self.btn_browse = QPushButton("Izberi datoteke")
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.setMinimumHeight(36)
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.owner = QLineEdit(self.service.default_owner())
        self.owner.setObjectName("EnterpriseSearch")
        self.owner.setMinimumHeight(36)
        self.module = QComboBox()
        self.module.setObjectName("EnterpriseFilter")
        self.module.setMinimumHeight(36)
        self.module.addItem("Brez povezave", "")
        for key, label in self.service.link_modules():
            self.module.addItem(label, key)
        self.entity = QComboBox()
        self.entity.setObjectName("EnterpriseFilter")
        self.entity.setMinimumHeight(36)
        self.entity.setEditable(True)
        grid.add_span(self.drop)
        grid.add("Datoteke", self.btn_browse, "Lastnik", self.owner)
        grid.add("Modul", self.module, "Povezano z", self.entity)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        self.btn_browse.clicked.connect(self._browse)
        self.module.currentIndexChanged.connect(self._reload_entities)
        self._reload_entities()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        self._add_urls(event.mimeData().urls())

    def _browse(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Dokumenti",
            "",
            "Dokumenti (*.pdf *.docx *.xlsx *.png *.jpg *.jpeg *.zip *.txt)",
        )
        self._add_paths([Path(item) for item in files])

    def _add_urls(self, urls) -> None:
        self._add_paths([Path(url.toLocalFile()) for url in urls if url.isLocalFile()])

    def _add_paths(self, paths: list[Path]) -> None:
        for path in paths:
            if path.is_file() and path not in self.paths:
                self.paths.append(path)
        if self.paths:
            self.drop.setText("\n".join(item.name for item in self.paths[:6]))

    def _reload_entities(self) -> None:
        self.entity.blockSignals(True)
        self.entity.clear()
        self.entity.addItem("—", None)
        for key, label in self.service.link_targets(self.module.currentData() or ""):
            self.entity.addItem(label, key)
        self.entity.blockSignals(False)

    def _accept(self) -> None:
        if not self.paths:
            return
        self.accept()

    def meta(self) -> dict:
        entity_id = self.entity.currentData()
        label = self.entity.currentText()
        if label == "—":
            label = ""
        return {
            "owner": self.owner.text().strip(),
            "module": self.module.currentData() or "",
            "entity_id": entity_id,
            "entity_label": label,
        }


class FolderDialog(EnterpriseDialog):

    def __init__(self, parent=None, title: str = "New Folder", name: str = "") -> None:
        super().__init__(parent, title=title, heading=title, size="SMALL", state_key="dialog.folder")
        self.setObjectName("UploadDialog")
        self.bind_save(self._accept)
        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.name = QLineEdit(name)
        self.name.setObjectName("EnterpriseSearch")
        self.name.setMinimumHeight(36)
        grid.add("Ime", self.name)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

    def _accept(self) -> None:
        if self.name.text().strip():
            self.accept()

    def value(self) -> str:
        return self.name.text().strip()


class MoveDialog(EnterpriseDialog):

    def __init__(self, parent=None, folders: list | None = None) -> None:
        super().__init__(
            parent,
            title="Premakni / Kopiraj",
            heading="Ciljna mapa",
            size="SMALL",
            state_key="dialog.move",
            save_text="Potrdi",
        )
        self.setObjectName("UploadDialog")
        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.folder = QComboBox()
        self.folder.setObjectName("EnterpriseFilter")
        self.folder.setMinimumHeight(36)
        self.folder.addItem("Dokumenti (koren)", None)
        for item in folders or []:
            self.folder.addItem(str(item[2]), item[0])
        grid.add("Mapa", self.folder)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

    def folder_id(self):
        return self.folder.currentData()

