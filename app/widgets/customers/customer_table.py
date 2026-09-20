from app.widgets.tables.enterprise_table import EnterpriseTable


class CustomerTable(EnterpriseTable):
    def __init__(self, parent=None):
        super().__init__(parent, sorting=False)
