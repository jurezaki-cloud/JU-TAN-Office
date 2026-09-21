"""Premium document editor UI shell — Invoice / Offer / Order dialogs."""

from app.widgets.document_editor.customer_panel import DocumentCustomerPanel
from app.widgets.document_editor.document_header import DocumentEditorHeader
from app.widgets.document_editor.document_workspace import DocumentWorkspace
from app.widgets.document_editor.items_panel import DocumentItemsPanel
from app.widgets.document_editor.totals_panel import DocumentTotalsPanel

__all__ = [
    "DocumentCustomerPanel",
    "DocumentEditorHeader",
    "DocumentItemsPanel",
    "DocumentTotalsPanel",
    "DocumentWorkspace",
]
