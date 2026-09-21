from PySide6.QtWidgets import QHeaderView

from app.widgets.tables.enterprise_table import EnterpriseTable


class OfferTable(EnterpriseTable):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EnterpriseTable")
        self.setMinimumHeight(280)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(72)
        header.setDefaultSectionSize(120)
