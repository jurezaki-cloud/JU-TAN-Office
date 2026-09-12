from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QTableWidget, QTableWidgetItem

from app.core.ui.table_menu import populate_table_menu


class ReportTable(QTableWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(0, 1, parent)
        self.setObjectName("EnterpriseTable")
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMinimumHeight(240)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos) -> None:
        menu = QMenu(self)
        populate_table_menu(menu, self)
        menu.exec(self.viewport().mapToGlobal(pos))

    def set_report(self, headers: list[str], rows: list[list]) -> None:
        self.clear()
        self.setColumnCount(len(headers) or 1)
        self.setHorizontalHeaderLabels(headers or ["—"])
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(str(value if value is not None else ""))
                if c == len(row) - 1:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.setItem(r, c, item)
