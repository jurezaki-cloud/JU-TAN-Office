from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

# Shell module context — authoritative page title (no PageHeader H1 duplicate).
PAGE_CONTEXT = {
    0: ("Nadzorna plošča", "Pregled poslovanja in ključnih kazalnikov"),
    1: ("Računi", "Pregled, iskanje in upravljanje izdanih računov"),
    2: ("Stranke", "Register strank in kontaktni podatki"),
    3: ("Ponudbe", "Priprava, spremljanje in pretvorba ponudb"),
    4: ("Artikli", "Katalog artiklov in cenik"),
    5: ("Podjetje", "Osnovni podatki, davčni status in kontakt"),
    6: ("Plačila", "Terjatve in prejeta plačila"),
    7: ("Analitika", "Poslovni pregled in grafi"),
    8: ("Nastavitve", "Konfiguracija aplikacije, dostopa in sistema"),
    9: ("Naročila", "Spremljanje naročil, dobav in statusov"),
    10: ("Skladišče", "Zaloga, gibanja in inventura"),
    11: ("Dobavitelji", "Dobavitelji in nabavni partnerji"),
    12: ("Nabava", "Nabavna naročila in prevzemi"),
    13: ("Dokumenti", "Centralni arhiv dokumentov"),
    14: ("CRM", "Pipeline, stranke 360 in follow-up"),
    15: ("Poročila", "Centralna poročila in izvozi"),
    16: ("Avtomatizacija", "Poslovna pravila, razpored in dnevnik"),
    17: ("Potni nalogi", "Evidenca potnih nalogov in obračunov"),
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
