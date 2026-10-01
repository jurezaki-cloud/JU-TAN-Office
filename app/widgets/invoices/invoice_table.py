from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHeaderView

from app.widgets.tables.enterprise_table import EnterpriseTable


class InvoiceTable(EnterpriseTable):
    COLUMN_WIDTHS = {
        0: 88,   # Šifra
        1: 220,  # Artikel
        2: 88,   # Količina
        3: 56,   # EM
        4: 100,  # Cena
        5: 88,   # Popust
        6: 72,   # DDV
        7: 110,  # Skupaj
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EnterpriseTable")
        self.setMinimumHeight(220)
        self.verticalHeader().setDefaultSectionSize(44)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(56)
        header.setDefaultSectionSize(100)
        # Apply preferred widths once a model is attached.
        self.horizontalHeader().sectionCountChanged.connect(self._apply_column_widths)

    def setModel(self, model) -> None:  # noqa: N802 — Qt API
        super().setModel(model)
        self._apply_column_widths()

    def _has_items_layout(self) -> bool:
        model = self.model()
        return model is not None and model.columnCount() >= len(self.COLUMN_WIDTHS)

    def _apply_column_widths(self, *_args) -> None:
        if not self._has_items_layout():
            return
        header = self.horizontalHeader()
        for col, width in self.COLUMN_WIDTHS.items():
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            header.resizeSection(col, width)
        # Artikel absorbs remaining space.
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(False)
        self.updateGeometry()

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt API
        """Wide enough for every visible column at its preferred width."""
        hint = super().sizeHint()
        if not self._has_items_layout():
            return hint
        columns = sum(width for col, width in self.COLUMN_WIDTHS.items() if not self.isColumnHidden(col))
        width = columns + 2 * self.frameWidth() + self.verticalScrollBar().sizeHint().width()
        return QSize(max(hint.width(), width), hint.height())
