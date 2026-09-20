from PySide6.QtCore import QAbstractTableModel, Qt

from app.modules.automation.automation_repository import TRIGGER_LABELS, SCHEDULE_KINDS
from app.widgets.tables.enterprise_table import EnterpriseTable

SCHEDULE_LABELS = dict(SCHEDULE_KINDS)


class AutomationTableModel(QAbstractTableModel):
    headers = ["ID", "Ime", "Sprožilec", "Stanje", "Prioriteta", "Razpored", "Zadnji zagon"]

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
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.TextAlignmentRole):
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter | Qt.AlignLeft
        row = self.rows[index.row()]
        column = index.column()
        if column == 0:
            return row[0]
        if column == 1:
            return row[1]
        if column == 2:
            return TRIGGER_LABELS.get(row[2], row[2])
        if column == 3:
            return "Omogočeno" if row[3] else "Onemogočeno"
        if column == 4:
            return row[4]
        if column == 5:
            return SCHEDULE_LABELS.get(row[5], row[5] or "—")
        return row[7] or "—"

    def refresh(self, rows: list) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class AutomationTable(EnterpriseTable):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model_ref = AutomationTableModel()
        self.setModel(self.model_ref)

    def current_id(self):
        index = self.currentIndex()
        if not index.isValid():
            return None
        return self.model_ref.rows[index.row()][0]
