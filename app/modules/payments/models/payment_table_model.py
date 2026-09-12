from PySide6.QtCore import Qt, QAbstractTableModel, QSize

from app.widgets.invoices.status_badge import invoice_badge


class PaymentTableModel(QAbstractTableModel):

    headers = [
        "Račun",
        "Stranka",
        "Datum",
        "Rok",
        "Znesek",
        "Status",
    ]

    def __init__(self, rows=None):
        super().__init__()
        self.rows = rows or []

    def refresh(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None

        row = self.rows[index.row()]

        if role == Qt.DisplayRole:
            column = index.column()
            if column == 0:
                return row[1]
            if column == 1:
                return row[2]
            if column == 2:
                return row[3]
            if column == 3:
                return row[4] or "—"
            if column == 4:
                try:
                    return f"{float(row[5]):,.2f} €".replace(",", " ")
                except (TypeError, ValueError):
                    return "0.00 €"
            if column == 5:
                return invoice_badge(row[6], row[4])

        if role == Qt.TextAlignmentRole:
            if index.column() in (2, 3, 5):
                return Qt.AlignCenter
            if index.column() == 4:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.SizeHintRole:
            return QSize(0, 48)

        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def invoice_id(self, row):
        return self.rows[row][0]

    def badge_at(self, row):
        data = self.rows[row]
        return invoice_badge(data[6], data[4])
