"""Ctrl+K: search modules and permitted Office records."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from app.core.permissions import can_open_page
from app.services.global_search import search_records

PAGES = [
    (0, "Dashboard"), (1, "Računi"), (2, "Stranke"),
    (3, "Ponudbe"), (4, "Artikli"), (5, "Podjetje"),
    (6, "Plačila"), (7, "Analitika"), (8, "Nastavitve"),
    (9, "Naročila"), (10, "Skladišče"), (11, "Dobavitelji"),
    (12, "Nabava"), (13, "Dokumenti"), (14, "CRM"),
    (15, "Poročila"), (16, "Avtomatizacija"),
    (17, "Potni nalogi"), (18, "Predračuni"),
]


class CommandPalette(QDialog):
    def __init__(self, parent=None, initial_query: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Globalno iskanje")
        self.setModal(True)
        self.setObjectName("CommandPalette")
        self.resize(560, 440)
        layout = QVBoxLayout(self)
        self.query = QLineEdit()
        self.query.setPlaceholderText("Stranka, številka dokumenta, artikel ali modul…")
        self.list = QListWidget()
        layout.addWidget(self.query)
        layout.addWidget(self.list)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(160)
        self._timer.timeout.connect(lambda: self._fill(self.query.text()))
        self.query.textChanged.connect(lambda _: self._timer.start())
        self.query.returnPressed.connect(self._choose_current)
        self.list.itemActivated.connect(self._accept)
        self.query.setText(initial_query)
        self._fill(initial_query)
        self.query.setFocus()
        self._chosen = None

    def _fill(self, text: str) -> None:
        needle = (text or "").strip().casefold()
        self.list.clear()
        for index, title in PAGES:
            if not can_open_page(index) or (needle and needle not in title.casefold()):
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, (index, ""))
            self.list.addItem(item)
        if len(needle) >= 2:
            for hit in search_records(text):
                item = QListWidgetItem(f"{hit.kind}: {hit.title}  ·  #{hit.record_id}")
                item.setData(Qt.UserRole, (hit.page, hit.query))
                self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _choose_current(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            self._accept(item)

    def _accept(self, item: QListWidgetItem) -> None:
        self._chosen = item.data(Qt.UserRole)
        self.accept()

    def chosen_index(self) -> int | None:
        if self._chosen is None:
            self._choose_current()
        return self._chosen[0] if self._chosen is not None else None

    def chosen_query(self) -> str:
        return self._chosen[1] if self._chosen is not None else ""
