from app.widgets.common.list_status_bar import DocumentListStatusBar


class OfferStatusBar(DocumentListStatusBar):
    def __init__(self, parent=None):
        super().__init__("Ponudbe", parent)
        self.setObjectName("OfferStatusBar")
