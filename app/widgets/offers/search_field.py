from app.widgets.common.enterprise_search import EnterpriseSearchField


class OfferSearch(EnterpriseSearchField):
    def __init__(self, parent=None):
        super().__init__(
            "Išči številko ponudbe ali stranko...",
            object_name="OfferSearch",
            parent=parent,
        )
