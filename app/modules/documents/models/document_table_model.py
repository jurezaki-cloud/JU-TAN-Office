from PySide6.QtCore import QAbstractTableModel, QSize, Qt


class DocumentTableModel(QAbstractTableModel):

    headers = ["Ime", "Tip", "Velikost", "Datum", "Povezano z", "Lastnik"]

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
            linked = ""
            module = str(row[10] or "").strip()
            label = str(row[12] or "").strip()
            if module and label:
                linked = f"{module}: {label}"
            else:
                linked = module or label or "—"
            values = (
                row[2],
                "Mapa" if row[3] else (row[7] or "").upper(),
                "—" if row[3] else _size(row[8]),
                str(row[13] or "")[:19].replace("T", " "),
                linked,
                row[9] or "—",
            )
            return values[index.column()]
        if role == Qt.TextAlignmentRole:
            if index.column() in (1, 3):
                return Qt.AlignCenter
            if index.column() == 2:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.SizeHintRole:
            return QSize(0, 48)
        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def document_id(self, row: int):
        return self.rows[row][0]

    def is_folder(self, row: int) -> bool:
        return bool(self.rows[row][3])


def _size(value) -> str:
    try:
        size = int(value or 0)
    except (TypeError, ValueError):
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
