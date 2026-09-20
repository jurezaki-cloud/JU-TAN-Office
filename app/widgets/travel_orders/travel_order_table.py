from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget


class TravelOrderTable(QTableWidget):
    """QTableWidget styled as EnterpriseTable for travel-order rows."""

    def __init__(self, parent=None) -> None:
        super().__init__(0, 8, parent)
        self.setObjectName("EnterpriseTable")
        self.setHorizontalHeaderLabels(
            ["Številka", "Zaposleni", "Relacija", "Odhod", "Prihod", "Km", "Skupaj", "Status"]
        )
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)
        self.setMinimumHeight(240)
