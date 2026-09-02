from PySide6.QtCore import Qt, QAbstractTableModel


class OfferTableModel(QAbstractTableModel):

    headers = [
        "Številka",
        "Stranka",
        "Datum",
        "Velja do",
        "Status",
        "Skupaj (€)"
    ]

    def __init__(self, offers=None):
        super().__init__()
        self.offers = offers or []

    def refresh(self, offers):
        self.beginResetModel()
        self.offers = offers
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.offers)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):

        if not index.isValid():
            return None

        offer = self.offers[index.row()]

        if role == Qt.DisplayRole:

            column = index.column()

            if column == 0:
                return offer[1]

            elif column == 1:
                return offer[2]

            elif column == 2:
                return offer[3]

            elif column == 3:
                return offer[4]

            elif column == 4:
                return offer[5]

            elif column == 5:
                return f"{offer[6]:.2f}"

        if role == Qt.TextAlignmentRole:

            if index.column() == 5:
                return Qt.AlignRight | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role):

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

        return None