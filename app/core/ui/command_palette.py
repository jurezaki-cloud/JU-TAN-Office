"""Ctrl+K — hitri ukazi in skok na module."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

PAGES = [
    (0, "Dashboard"),
    (1, "Računi"),
    (2, "Stranke"),
    (3, "Ponudbe"),
    (4, "Artikli"),
    (5, "Podjetje"),
    (6, "Plačila"),
    (7, "Analitika"),
    (8, "Nastavitve"),
    (9, "Naročila"),
    (10, "Skladišče"),
    (11, "Dobavitelji"),
    (12, "Nabava"),
    (13, "Dokumenti"),
    (14, "CRM"),
    (15, "Poročila"),
    (16, "Automation"),
]


class CommandPalette(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Hitri ukazi")
        self.setModal(True)
        self.setObjectName("CommandPalette")
        self.resize(440, 360)
        layout = QVBoxLayout(self)
        self.query = QLineEdit()
        self.query.setPlaceholderText("Išči modul ali ukaz…")
        self.list = QListWidget()
        layout.addWidget(self.query)
        layout.addWidget(self.list)
        self._fill("")
        self.query.textChanged.connect(self._fill)
        self.list.itemActivated.connect(self._accept)
        self.query.setFocus()

    def _fill(self, text: str) -> None:
        needle = (text or "").casefold()
        self.list.clear()
        for index, title in PAGES:
            if needle and needle not in title.casefold():
                continue
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, index)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _accept(self, item: QListWidgetItem) -> None:
        self._chosen = item.data(Qt.UserRole)
        self.accept()

    def chosen_index(self) -> int | None:
        item = self.list.currentItem()
        if item is None:
            return None
        return int(item.data(Qt.UserRole))
