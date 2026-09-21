from app.widgets.common.list_status_bar import DocumentListStatusBar


class OrderStatusBar(DocumentListStatusBar):
    def __init__(self, parent=None):
        super().__init__("Naročila", parent)
        self.setObjectName("OrderStatusBar")
