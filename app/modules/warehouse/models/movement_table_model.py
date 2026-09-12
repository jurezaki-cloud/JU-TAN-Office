from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QSize, Qt


class MovementTableModel(QAbstractTableModel):

    headers = [
        "Datum",
        "Tip",
        "Artikel",
        "Količina",
        "Uporabnik",
        "Opomba",
    ]

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = rows or []

    def refresh(self, rows: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=None) -> int:
        return len(self.rows)

    def columnCount(self, parent=None) -> int:
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            article = " ".join(
                part for part in (
                    str(row.get("article_code") or ""),
                    str(row.get("article_name") or ""),
                ) if part
            ).strip()
            qty = row.get("quantity") or 0
            try:
                number = float(qty)
                qty_text = str(int(number)) if number.is_integer() else f"{number:.2f}"
            except (TypeError, ValueError):
                qty_text = str(qty)
            values = (
                str(row.get("date") or "")[:19].replace("T", " "),
                str(row.get("type") or ""),
                article,
                qty_text,
                str(row.get("user") or ""),
                str(row.get("note") or ""),
            )
            return values[column]

        if role == Qt.TextAlignmentRole:
            if column in (0, 1):
                return Qt.AlignCenter
            if column == 3:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.SizeHintRole:
            return QSize(0, 48)

        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
