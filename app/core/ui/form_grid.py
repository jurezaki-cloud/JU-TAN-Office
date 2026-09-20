"""Dvo-stolpčni obrazec (QGridLayout)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from app.core.ui.sizes import LAYOUT_SPACING


class FormGrid:
    def __init__(self) -> None:
        self.layout = QGridLayout()
        self.layout.setHorizontalSpacing(16)
        self.layout.setVerticalSpacing(LAYOUT_SPACING)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(3, 1)
        self._row = 0

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label

    def add(self, left_label: str, left: QWidget, right_label: str | None = None, right: QWidget | None = None) -> None:
        self.layout.addWidget(self._label(left_label), self._row, 0)
        self.layout.addWidget(left, self._row, 1)
        if right_label and right is not None:
            self.layout.addWidget(self._label(right_label), self._row, 2)
            self.layout.addWidget(right, self._row, 3)
        self._row += 1

    def add_span(self, widget: QWidget) -> None:
        self.layout.addWidget(widget, self._row, 0, 1, 4)
        self._row += 1

    def add_full(self, label: str, widget: QWidget) -> None:
        self.layout.addWidget(self._label(label), self._row, 0)
        self.layout.addWidget(widget, self._row, 1, 1, 3)
        self._row += 1
