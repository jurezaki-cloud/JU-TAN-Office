"""Responsive ERP workspace layout for document editors."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from app.widgets.document_editor.customer_panel import DocumentCustomerPanel
from app.widgets.document_editor.document_header import DocumentEditorHeader
from app.widgets.document_editor.items_panel import DocumentItemsPanel
from app.widgets.document_editor.totals_panel import DocumentTotalsPanel


class DocumentWorkspace(QWidget):
    """Header + horizontal splitter (customer | items) + totals."""

    def __init__(self, *, doc_kind: str = "Račun", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentWorkspace")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)

        self.header = DocumentEditorHeader(doc_kind=doc_kind)
        root.addWidget(self.header)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("DocumentEditorSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(8)

        self.customer_panel = DocumentCustomerPanel()
        self.items_panel = DocumentItemsPanel()

        left = QWidget()
        left.setObjectName("DocumentEditorLeft")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.customer_panel)

        right = QWidget()
        right.setObjectName("DocumentEditorRight")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.items_panel)

        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setSizes([340, 720])
        root.addWidget(self.splitter, 1)

        self.totals_panel = DocumentTotalsPanel()
        root.addWidget(self.totals_panel)
