from PySide6.QtCore import QAbstractTableModel, Qt

from app.widgets.tables.enterprise_table import EnterpriseTable


class ExecutionLogModel(QAbstractTableModel):
    headers = [
        "Začetek", "Konec", "Trajanje (ms)", "Rezultat",
        "Uporabnik", "Napaka", "Ponovitve", "Pravilo",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.rows: list = []

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        mapping = {
            0: row[3],
            1: row[4],
            2: row[5],
            3: row[6],
            4: row[7],
            5: row[8],
            6: row[9],
            7: row[1],
        }
        return mapping.get(index.column(), "")

    def refresh(self, rows: list) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class ExecutionLogTable(EnterpriseTable):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model_ref = ExecutionLogModel()
        self.setModel(self.model_ref)
