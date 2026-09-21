from app.widgets.common.enterprise_search import EnterpriseSearchField


class InvoiceSearch(EnterpriseSearchField):
    def __init__(self, parent=None):
        super().__init__(
            "Išči številko računa ali stranko...",
            object_name="InvoiceSearch",
            parent=parent,
        )
