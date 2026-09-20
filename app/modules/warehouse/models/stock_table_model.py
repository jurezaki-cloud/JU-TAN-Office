from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QSize, Qt

from app.modules.warehouse.warehouse_service import StockRow


class StockTableModel(QAbstractTableModel):

    headers = [
        "Šifra",
        "Naziv",
        "Skladišče",
        "Na zalogi",
        "Rezervirano",
        "Prosto",
        "Minimalna zaloga",
        "Status",
    ]

    def __init__(self, rows: list[StockRow] | None = None) -> None:
        super().__init__()
        self.rows: list[StockRow] = rows or []

    def refresh(self, rows: list[StockRow]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=None) -> int:
        return len(self.rows)

    def columnCount(self, parent=None) -> int:
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            values = (
                row.code,
                row.name,
                row.warehouse,
                _qty(row.qty),
                _qty(row.reserved),
                _qty(row.free),
                _qty(row.min_qty),
                row.status,
            )
            return values[column]

        if role == Qt.TextAlignmentRole:
            if column in (3, 4, 5, 6):
                return Qt.AlignRight | Qt.AlignVCenter
            if column in (2, 7):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.SizeHintRole:
            return QSize(0, 48)

        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def row_at(self, index: int) -> StockRow:
        return self.rows[index]


def _qty(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".replace(".", ",")
