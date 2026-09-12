from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.modules.documents.documents_controller import DocumentsController
from app.modules.documents.models.document_table_model import DocumentTableModel
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.documents.document_filters import DocumentFilters
from app.widgets.documents.document_table import DocumentTable
from app.widgets.documents.document_toolbar import DocumentToolbar
from app.widgets.documents.preview_panel import PreviewPanel
from app.widgets.documents.upload_dialog import FolderDialog, MoveDialog, UploadDialog


class DocumentsPage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentsPage")
        self.controller = DocumentsController()
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Dokumenti")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(16)
        self.kpi_total = KpiCard("Skupno dokumentov", "0", "Datoteke")
        self.kpi_pdf = KpiCard("PDF", "0", "Adobe PDF")
        self.kpi_images = KpiCard("Slike", "0", "PNG / JPG")
        self.kpi_word = KpiCard("Word", "0", "DOCX")
        self.kpi_excel = KpiCard("Excel", "0", "XLSX")
        self.kpi_size = KpiCard("Velikost arhiva", "0 B", "data/documents")
        for card in (
            self.kpi_total,
            self.kpi_pdf,
            self.kpi_images,
            self.kpi_word,
            self.kpi_excel,
            self.kpi_size,
        ):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        self.actions = DocumentToolbar()
        layout.addWidget(self.actions)
        self.filters = DocumentFilters()
        self.search = self.filters.search
        layout.addWidget(self.filters)

        self.table = DocumentTable()
        self.model = DocumentTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(1, StatusBadgeDelegate(self.table))
        self.preview = PreviewPanel()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        splitter = QSplitter()
        splitter.setObjectName("DocumentsSplitter")
        splitter.addWidget(table_card)
        splitter.addWidget(self.preview)
        splitter.setSizes([780, 320])
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        self.actions.upload_clicked.connect(self.upload)
        self.actions.folder_clicked.connect(self.new_folder)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.download_clicked.connect(self.download)
        self.actions.delete_clicked.connect(self.delete)
        self.actions.export_clicked.connect(self.export_list)
        self.actions.up_clicked.connect(self.go_up)
        self.filters.filter_changed.connect(self.refresh)
        self.table.clicked.connect(self._preview)
        self.table.selectionModel().selectionChanged.connect(self._preview)
        self.table.doubleClicked.connect(self._open_or_enter)
        self.table.extra_menu.connect(self._menu)
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.documents", splitters=[splitter], tables=[self.table], fields=[self.search])
        self.refresh()

    def refresh(self) -> None:
        self.filters.fill_modules(self.controller.service.link_modules())
        self.filters.fill_owners(self.controller.owners())
        self.filters.path.setText(self.controller.breadcrumb())
        rows = self.controller.list_rows(
            query=self.search.text(),
            kind=self.filters.kind.currentData() or "all",
            module=self.filters.module.currentData() or "all",
            owner=self.filters.owner.currentData() or "all",
            date_filter=self.filters.date_mode.currentData() or "all",
            selected_date=self.filters.date.date().toString("yyyy-MM-dd"),
        )
        self.model.refresh(rows)
        kpis = self.controller.kpis()
        self.kpi_total.set_value(str(kpis["total"]))
        self.kpi_pdf.set_value(str(kpis["pdf"]))
        self.kpi_images.set_value(str(kpis["images"]))
        self.kpi_word.set_value(str(kpis["word"]))
        self.kpi_excel.set_value(str(kpis["excel"]))
        self.kpi_size.set_value(_size(kpis["size"]))
        self._preview()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        owner = self.controller.service.default_owner()
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            try:
                self.controller.upload(Path(url.toLocalFile()), owner=owner)
            except Exception as exc:
                QMessageBox.warning(self, "Upload", str(exc))
        self.refresh()

    def upload(self) -> None:
        dialog = UploadDialog(self, self.controller.service)
        if not dialog.exec():
            return
        meta = dialog.meta()
        for path in dialog.paths:
            try:
                self.controller.upload(path, **meta)
            except Exception as exc:
                QMessageBox.warning(self, "Upload", str(exc))
        self.refresh()

    def new_folder(self) -> None:
        dialog = FolderDialog(self)
        if dialog.exec():
            self.controller.new_folder(dialog.value(), self.controller.service.default_owner())
            self.refresh()

    def go_up(self) -> None:
        self.controller.go_up()
        self.refresh()

    def download(self) -> None:
        document_id = self._selected_id()
        row = self._selected_row()
        if document_id is None or row is None or row[3]:
            QMessageBox.information(self, "Dokumenti", "Izberi datoteko.")
            return
        target, _ = QFileDialog.getSaveFileName(self, "Download", row[2])
        if not target:
            return
        self.controller.download(document_id, Path(target))
        QMessageBox.information(self, "Download", f"Shranjeno:\n{target}")

    def delete(self) -> None:
        document_id = self._selected_id()
        if document_id is None:
            QMessageBox.information(self, "Dokumenti", "Izberi dokument.")
            return
        if QMessageBox.question(self, "Dokumenti", "Izbrisati?") != QMessageBox.Yes:
            return
        self.controller.delete(document_id)
        self.refresh()

    def export_list(self) -> None:
        start = str(self.controller.export_start_path())
        path, _ = QFileDialog.getSaveFileName(self, "Export List", start, "Excel (*.xlsx)")
        if not path:
            return
        self.controller.export_excel(Path(path), self.model.rows)
        QMessageBox.information(self, "Excel", f"Seznam shranjen:\n{path}")

    def rename(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        dialog = FolderDialog(self, "Rename", str(row[2]))
        if dialog.exec():
            self.controller.rename(row[0], dialog.value())
            self.refresh()

    def move(self, copy: bool = False) -> None:
        document_id = self._selected_id()
        if document_id is None:
            return
        dialog = MoveDialog(self, self.controller.folders())
        if not dialog.exec():
            return
        if copy:
            self.controller.copy(document_id, dialog.folder_id())
        else:
            self.controller.move(document_id, dialog.folder_id())
        self.refresh()

    def open_file(self) -> None:
        document_id = self._selected_id()
        path = self.controller.path_for_id(document_id) if document_id else None
        if path is None or not path.exists():
            QMessageBox.information(self, "Dokumenti", "Datoteke ni mogoče odpreti.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _open_or_enter(self) -> None:
        row = self._selected_row()
        if row is None:
            return
        if row[3]:
            self.controller.enter_folder(row[0])
            self.refresh()
            return
        self.open_file()

    def _menu(self, menu, pos) -> None:
        if self._selected_id() is None:
            return
        menu.addSeparator()
        for text, slot in (
            ("Open", self.open_file),
            ("Rename", self.rename),
            ("Move", lambda: self.move(False)),
            ("Copy", lambda: self.move(True)),
            ("Download", self.download),
            ("Delete", self.delete),
        ):
            action = QAction(text, menu)
            action.triggered.connect(slot)
            menu.addAction(action)

    def _selected_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.document_id(indexes[0].row())

    def _selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.rows[indexes[0].row()]

    def _preview(self, *_args) -> None:
        row = self._selected_row()
        path = self.controller.path_for_id(row[0]) if row else None
        self.preview.show_row(row, path)


def _size(value) -> str:
    try:
        size = int(value or 0)
    except (TypeError, ValueError):
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
