from PySide6.QtCore import Qt, QAbstractTableModel


class CustomerTableModel(QAbstractTableModel):

    headers = [
        "ID",
        "Podjetje",
        "Kontakt",
        "Telefon",
        "E-pošta",
        "Mesto",
    ]

    def __init__(self, customers=None):
        super().__init__()
        self.customers = customers or []

    def rowCount(self, parent=None):
        return len(self.customers)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):

        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self.customers[index.row()][index.column()]

        return None

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.headers[section]

        return section + 1

    def refresh(self, customers):
        self.beginResetModel()
        self.customers = customers
        self.endResetModel()