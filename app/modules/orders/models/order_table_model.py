from PySide6.QtCore import Qt, QAbstractTableModel, QSize

from app.widgets.orders.status_badge import order_badge


class OrderTableModel(QAbstractTableModel):

    headers = [
        "Številka",
        "Stranka",
        "Datum",
        "Dobava",
        "Status",
        "Skupaj (€)",
    ]

    def __init__(self, orders=None):
        super().__init__()
        self.orders = orders or []

    def refresh(self, orders):
        self.beginResetModel()
        self.orders = orders
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.orders)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):

        if not index.isValid():
            return None

        order = self.orders[index.row()]

        if role == Qt.DisplayRole:
            column = index.column()
            if column == 0:
                return order[1]
            if column == 1:
                return order[2]
            if column == 2:
                return order[3]
            if column == 3:
                return order[4]
            if column == 4:
                return order_badge(order[5], order[4])
            if column == 5:
                try:
                    return f"{float(order[6]):,.2f} €".replace(",", " ")
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

    def order_id(self, row):
        return self.orders[row][0]

    def badge_at(self, row):
        order = self.orders[row]
        return order_badge(order[5], order[4])
