from app.widgets.tables.enterprise_table import EnterpriseTable


class DocumentTable(EnterpriseTable):

    def __init__(self, parent=None) -> None:
        super().__init__(parent, sorting=False)
        self.setAcceptDrops(True)
