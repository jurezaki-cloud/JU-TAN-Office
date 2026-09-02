from PySide6.QtCore import Qt, QAbstractTableModel


class ArticleTableModel(QAbstractTableModel):

    headers = [
        "ID",
        "Šifra",
        "Naziv",
        "Enota",
        "Cena",
        "DDV %",
    ]

    def __init__(self, articles=None):
        super().__init__()
        self.articles = articles or []

    def rowCount(self, parent=None):
        return len(self.articles)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):

        if not index.isValid():
            return None

        if role == Qt.DisplayRole:

            value = self.articles[index.row()][index.column()]

            # Lepši prikaz cene
            if index.column() == 4:
                return f"{value:.2f} €"

            # Lepši prikaz DDV
            if index.column() == 5:
                return f"{value:.0f}%"

            return value

        if role == Qt.TextAlignmentRole:

            if index.column() in (0, 4, 5):
                return Qt.AlignCenter

        return None

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.headers[section]

        return section + 1

    def refresh(self, articles):

        self.beginResetModel()

        self.articles = articles

        self.endResetModel()