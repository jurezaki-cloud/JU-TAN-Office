from PySide6.QtCore import Qt, QAbstractTableModel

from app.utils.money import format_eur, money


class InvoiceItemsModel(QAbstractTableModel):

    HEADERS = [
        "Šifra",
        "Artikel",
        "Količina",
        "EM",
        "Cena",
        "Popust %",
        "DDV",
        "Skupaj",
    ]

    # Right-align numeric business columns.
    _NUMERIC_COLUMNS = frozenset({2, 4, 5, 6, 7})

    def __init__(self):
        super().__init__()
        self.items = []

    def rowCount(self, parent=None):
        return len(self.items)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role):
        if not index.isValid():
            return None

        row = self.items[index.row()]
        col = index.column()

        if role == Qt.TextAlignmentRole:
            if col in self._NUMERIC_COLUMNS:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        if role == Qt.DisplayRole:
            value = row[col] if col < len(row) else None
            return self._format_display(col, value)

        if role == Qt.ToolTipRole and col == 1:
            text = str(row[1] if len(row) > 1 else "").strip()
            description = str(row[9] or "").strip() if len(row) > 9 else ""
            return "\n".join(part for part in (text, description) if part) or None

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        if role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            if section in self._NUMERIC_COLUMNS:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)
        return None

    def refresh(self, items):
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def add_item(self, row):
        self.beginResetModel()
        self.items.append(row)
        self.endResetModel()

    def remove_row(self, row):
        self.beginResetModel()
        del self.items[row]
        self.endResetModel()

    def total(self):
        total = 0
        for row in self.items:
            total += float(row[7])
        return total

    @staticmethod
    def _format_display(column: int, value):
        if value is None:
            return ""
        if column in (4, 7):
            try:
                return format_eur(money(value))
            except Exception:
                return str(value)
        if column == 2:
            try:
                qty = float(value)
                if qty.is_integer():
                    return str(int(qty))
                return f"{qty:.2f}".rstrip("0").rstrip(".")
            except Exception:
                return str(value)
        if column == 5:
            try:
                return f"{float(value):.1f} %"
            except Exception:
                return str(value)
        if column == 6:
            try:
                return f"{float(value):.0f} %"
            except Exception:
                return str(value)
        return str(value)
