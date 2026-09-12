from PySide6.QtCore import Qt, QAbstractTableModel


class InvoiceItemsModel(QAbstractTableModel):

    HEADERS = [
        "Šifra",
        "Artikel",
        "Količina",
        "EM",
        "Cena",
        "DDV",
        "Skupaj",
    ]

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

        if role == Qt.DisplayRole:
            return self.items[index.row()][index.column()]

        return None

    def headerData(self, section, orientation, role):

        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]

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
            total += float(row[6])

        return total