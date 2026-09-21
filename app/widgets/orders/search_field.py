from app.widgets.common.enterprise_search import EnterpriseSearchField


class OrderSearch(EnterpriseSearchField):
    def __init__(self, parent=None):
        super().__init__(
            "Išči številko naročila ali stranko...",
            object_name="OrderSearch",
            parent=parent,
        )
