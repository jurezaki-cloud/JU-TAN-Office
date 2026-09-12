from PySide6.QtCore import Qt, QAbstractTableModel, QSize

from app.widgets.offers.status_badge import offer_badge


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
                return offer_badge(offer[5], offer[4])

            elif column == 5:
                try:
                    return f"{float(offer[6]):,.2f} €".replace(",", " ")
                except (TypeError, ValueError):
                    return "0.00 €"

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

    def offer_id(self, row):
        return self.offers[row][0]

    def badge_at(self, row):
        offer = self.offers[row]
        return offer_badge(offer[5], offer[4])
