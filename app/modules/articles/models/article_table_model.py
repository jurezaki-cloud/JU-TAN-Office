from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize


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

        row = self.articles[index.row()]
        value = row[index.column()]

        if role == Qt.DisplayRole:

            if index.column() == 4:
                return f"{float(value):,.2f} €".replace(",", " ")

            if index.column() == 5:
                try:
                    value = float(value)
                    if value == int(value):
                        return f"{int(value)} %"
                    return f"{value:g} %"
                except (TypeError, ValueError):
                    return str(value)

            return value

        if role == Qt.TextAlignmentRole:

            if index.column() in (0, 3, 4, 5):
                return Qt.AlignCenter

            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.SizeHintRole:
            return QSize(0, 48)

        return None

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.headers[section]

        return str(section + 1)

    def refresh(self, articles):

        self.beginResetModel()
        self.articles = articles
        self.endResetModel()

    def append_rows(self, rows):
        if not rows:
            return
        start = len(self.articles)
        self.beginInsertRows(QModelIndex(), start, start + len(rows) - 1)
        self.articles = list(self.articles) + list(rows)
        self.endInsertRows()

    # -----------------------------
    # NOVE METODE
    # -----------------------------

    def article(self, row):

        if row < 0 or row >= len(self.articles):
            return None

        return self.articles[row]

    def article_id(self, row):

        article = self.article(row)

        if article is None:
            return None

        return article[0]

    def count(self):
        return len(self.articles)

    def clear(self):
        self.refresh([])