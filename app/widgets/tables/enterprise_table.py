"""Skupna Enterprise tabela — enoten videz seznamov."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QMenu, QTableView

from app.core.ui.table_menu import populate_table_menu


class EnterpriseTable(QTableView):
    """Standardna vrstična tabela brez lokalnega stylesheeta."""

    extra_menu = Signal(object, object)

    def __init__(self, parent=None, *, sorting: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("EnterpriseTable")
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setShowGrid(False)
        self.setMouseTracking(True)
        self.setSortingEnabled(sorting)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self.setWordWrap(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)
        self.setMinimumHeight(240)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos) -> None:
        menu = QMenu(self)
        populate_table_menu(menu, self)
        self.extra_menu.emit(menu, pos)
        menu.exec(self.viewport().mapToGlobal(pos))
