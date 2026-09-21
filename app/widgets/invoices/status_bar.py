from app.widgets.common.list_status_bar import DocumentListStatusBar


class InvoiceStatusBar(DocumentListStatusBar):
    def __init__(self, parent=None):
        super().__init__("Računi", parent)
        self.setObjectName("InvoiceStatusBar")
