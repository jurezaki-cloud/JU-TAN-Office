from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize

from app.widgets.invoices.status_badge import invoice_badge


class InvoiceTableModel(QAbstractTableModel):

    HEADERS = [
        "ID",
        "Št. računa",
        "Datum",
        "Stranka",
        "Skupaj",
        "Status",
    ]

    def __init__(self, invoices=None):
        super().__init__()
        self.invoices = invoices or []

    def refresh(self, invoices):
        self.beginResetModel()
        self.invoices = invoices
        self.endResetModel()

    def append_rows(self, rows):
        if not rows:
            return
        start = len(self.invoices)
        self.beginInsertRows(QModelIndex(), start, start + len(rows) - 1)
        self.invoices = list(self.invoices) + list(rows)
        self.endInsertRows()

    def rowCount(self, parent=None):
        return len(self.invoices)

    def columnCount(self, parent=None):
        return len(self.HEADERS)

    def data(self, index, role):

        if not index.isValid():
            return None

        row = self.invoices[index.row()]
        value = row[index.column()]

        if role == Qt.DisplayRole:

            if index.column() == 4:
                try:
                    return f"{float(value):,.2f} €".replace(",", " ")
                except (TypeError, ValueError):
                    return "0,00 €"

            if index.column() == 5:
                due = row[6] if len(row) > 6 else None
                return invoice_badge(value, due)

            return value

        if role == Qt.TextAlignmentRole:

            if index.column() in (0, 2, 4, 5):
                return Qt.AlignCenter

            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.SizeHintRole:
            return QSize(0, 48)

        return None

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.HEADERS[section]

        return str(section + 1)

    def invoice_id(self, row):
        return self.invoices[row][0]

    def badge_at(self, row):
        data = self.invoices[row]
        due = data[6] if len(data) > 6 else None
        return invoice_badge(data[5], due)
