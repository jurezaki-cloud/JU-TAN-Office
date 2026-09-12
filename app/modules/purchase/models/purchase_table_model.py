from PySide6.QtCore import QAbstractTableModel, QSize, Qt


class PurchaseTableModel(QAbstractTableModel):

    headers = [
        "Številka",
        "Dobavitelj",
        "Datum",
        "Rok dobave",
        "Status",
        "Skupaj",
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
                row[3],
                row[4] or "—",
                row[5],
                _money(row[6]),
            )
            return values[index.column()]
        if role == Qt.TextAlignmentRole:
            if index.column() in (2, 3, 4):
                return Qt.AlignCenter
            if index.column() == 5:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.SizeHintRole:
            return QSize(0, 48)
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def purchase_id(self, row: int):
        return self.rows[row][0]


class PurchaseItemsModel(QAbstractTableModel):

    HEADERS = ["Artikel", "Količina", "Cena", "DDV", "Skupaj"]

    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict] = []

    def rowCount(self, parent=None) -> int:
        return len(self.items)

    def columnCount(self, parent=None) -> int:
        return len(self.HEADERS)

    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        item = self.items[index.row()]
        artikel = " — ".join(
            part for part in (str(item.get("code") or ""), str(item.get("name") or "")) if part
        )
        values = (
            artikel,
            _qty(item.get("quantity")),
            _money(item.get("price")),
            f"{float(item.get('vat') or 0):.1f} %",
            _money(item.get("total")),
        )
        return values[index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def refresh(self, items: list[dict]) -> None:
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def add_item(self, item: dict) -> None:
        self.beginResetModel()
        self.items.append(item)
        self.endResetModel()

    def remove_row(self, row: int) -> None:
        self.beginResetModel()
        del self.items[row]
        self.endResetModel()


def _money(value) -> str:
    try:
        return f"{float(value or 0):,.2f} €".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 €"


def _qty(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".replace(".", ",")
