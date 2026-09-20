"""Kontekstni meni tabele: copy, izvoz izbora, auto-fit."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractItemView, QApplication, QFileDialog, QHeaderView, QMenu


def _cell_text(view: QAbstractItemView, row: int, column: int) -> str:
    model = view.model()
    if model is None:
        return ""
    index = model.index(row, column)
    value = model.data(index, Qt.DisplayRole)
    return "" if value is None else str(value)


def _row_text(view: QAbstractItemView, row: int) -> str:
    model = view.model()
    if model is None:
        return ""
    parts = [_cell_text(view, row, col) for col in range(model.columnCount())]
    return "\t".join(parts)


def copy_cell(view: QAbstractItemView) -> None:
    index = view.currentIndex()
    if not index.isValid():
        return
    QApplication.clipboard().setText(_cell_text(view, index.row(), index.column()))


def copy_row(view: QAbstractItemView) -> None:
    index = view.currentIndex()
    if not index.isValid():
        return
    QApplication.clipboard().setText(_row_text(view, index.row()))


def export_selected(view: QAbstractItemView, parent=None) -> None:
    model = view.model()
    if model is None:
        return
    rows = sorted({index.row() for index in view.selectionModel().selectedIndexes()})
    if not rows:
        index = view.currentIndex()
        if index.isValid():
            rows = [index.row()]
    if not rows:
        return
    headers = [str(model.headerData(col, Qt.Horizontal) or "") for col in range(model.columnCount())]
    data = [[_cell_text(view, row, col) for col in range(model.columnCount())] for row in rows]
    path, _ = QFileDialog.getSaveFileName(
        parent or view,
        "Izvoz izbora",
        str(Path.home() / "izbor.xlsx"),
        "Excel (*.xlsx);;CSV (*.csv)",
    )
    if not path:
        return
    target = Path(path)
    if target.suffix.lower() != ".xlsx":
        lines = [";".join(headers)] + [";".join(row) for row in data]
        target.write_text("\n".join(lines), encoding="utf-8")
        return
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.title = "Izbor"
    sheet.append(headers)
    for row in data:
        sheet.append(row)
    book.save(target)


def auto_fit_columns(view: QAbstractItemView) -> None:
    header = view.horizontalHeader() if hasattr(view, "horizontalHeader") else None
    if header is None:
        return
    count = header.count()
    header.setSectionResizeMode(QHeaderView.ResizeToContents)
    view.resizeColumnsToContents()
    for index in range(count):
        header.setSectionResizeMode(index, QHeaderView.Interactive)
    header.setStretchLastSection(True)


def populate_table_menu(menu: QMenu, view: QAbstractItemView) -> None:
    cell = QAction("Copy Cell", menu)
    cell.triggered.connect(lambda: copy_cell(view))
    row = QAction("Copy Row", menu)
    row.triggered.connect(lambda: copy_row(view))
    export = QAction("Export Selected", menu)
    export.triggered.connect(lambda: export_selected(view, view.window()))
    fit = QAction("Auto Fit Columns", menu)
    fit.triggered.connect(lambda: auto_fit_columns(view))
    menu.addAction(cell)
    menu.addAction(row)
    menu.addAction(export)
    menu.addAction(fit)
