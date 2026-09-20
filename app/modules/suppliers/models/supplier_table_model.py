from PySide6.QtCore import QAbstractTableModel, QSize, Qt


class SupplierTableModel(QAbstractTableModel):

    headers = [
        "Naziv",
        "Davčna",
        "Kontakt",
        "Telefon",
        "Email",
        "Status",
        "Skupni promet",
    ]

    def __init__(self, rows=None) -> None:
        super().__init__()
        self.rows = rows or []

    def refresh(self, rows) -> None:
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
        if role == Qt.DisplayRole:
            values = (
                row[1],
                row[2] or "—",
                row[3] or "—",
                row[4] or "—",
                row[5] or "—",
                row[6] or "Active",
                _money(row[7]),
            )
            return values[index.column()]
        if role == Qt.TextAlignmentRole:
            if index.column() in (5,):
                return Qt.AlignCenter
            if index.column() == 6:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.SizeHintRole:
            return QSize(0, 48)
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def supplier_id(self, row: int):
        return self.rows[row][0]


def _money(value) -> str:
    try:
        return f"{float(value or 0):,.2f} €".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 €"
