from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

PAGE_CONTEXT = {
    0: ("Dashboard", "Pregled poslovanja in ključnih kazalnikov"),
    1: ("Računi", "Izdani računi in evidenca prometa"),
    2: ("Stranke", "Register strank in kontaktni podatki"),
    3: ("Ponudbe", "Ponudbe in predračuni"),
    4: ("Artikli", "Katalog artiklov in cenik"),
    5: ("Podjetje", "Podatki podjetja in identiteta"),
    6: ("Plačila", "Terjatve in prejeta plačila"),
    7: ("Analytics", "Business Intelligence"),
    8: ("Settings", "Application Configuration"),
    9: ("Naročila", "Naročila strank in dobava"),
    10: ("Skladišče", "Zaloga, gibanja in inventura"),
    11: ("Suppliers", "Dobavitelji in nabavni partnerji"),
    12: ("Purchase Orders", "Nabavna naročila in prevzemi"),
    13: ("Documents", "Centralni arhiv dokumentov"),
    14: ("CRM", "Pipeline, stranke 360 in follow-up"),
    15: ("Reports", "Centralna poročila in izvozi"),
    16: ("Automation", "Poslovna pravila, razpored in dnevnik izvajanja"),
}


class ToolbarTitle(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarTitleBlock")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 0, 8, 0)
        layout.setSpacing(0)

        self.title = QLabel()
        self.title.setObjectName("ToolbarModuleTitle")

        self.subtitle = QLabel()
        self.subtitle.setObjectName("ToolbarModuleSubtitle")

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)

        self.set_context(0)

    def set_context(self, page_index: int) -> None:
        title, subtitle = PAGE_CONTEXT.get(
            page_index,
            ("JU-TAN Office", "Enterprise"),
        )
        self.title.setText(title)
        self.subtitle.setText(subtitle)
