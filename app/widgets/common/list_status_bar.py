"""Premium footer status strip for document list pages."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

from app.theme.tokens import SPACE_1, SPACE_2, SPACE_4


class DocumentListStatusBar(QFrame):
    """Count + selection summary for invoice / offer / order lists."""

    def __init__(self, entity_label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentListStatusBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._entity_label = entity_label

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACE_4, SPACE_2, SPACE_4, SPACE_2)
        layout.setSpacing(SPACE_4)

        self.count_label = QLabel(f"{entity_label}: 0")
        self.count_label.setObjectName("DocumentListStatusCount")

        self.hint_label = QLabel("Dvoklik za urejanje")
        self.hint_label.setObjectName("DocumentListStatusHint")

        self.selected_label = QLabel("Izbrana vrstica: ni izbrane")
        self.selected_label.setObjectName("DocumentListStatusSelected")

        layout.addWidget(self.count_label)
        layout.addSpacing(SPACE_1)
        layout.addWidget(self.hint_label)
        layout.addStretch(1)
        layout.addWidget(self.selected_label)

    def set_count(self, count: int) -> None:
        self.count_label.setText(f"{self._entity_label}: {count}")

    def set_selected(self, name: str | None) -> None:
        if name:
            self.selected_label.setText(f"Izbrana vrstica: {name}")
        else:
            self.selected_label.setText("Izbrana vrstica: ni izbrane")
