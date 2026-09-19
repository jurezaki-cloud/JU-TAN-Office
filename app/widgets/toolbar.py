from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


PAGE_META = {
    0: ("Poslovni pregled", "Ključni podatki in stanje poslovanja"),
    1: ("Računi", "Izdani računi, statusi in plačila"),
    2: ("Stranke", "Kupci, kontakti in poslovni podatki"),
    3: ("Ponudbe", "Priprava in upravljanje ponudb"),
    4: ("Storitve", "Katalog storitev"),
    5: ("Artikli", "Izdelki, cene in davčne stopnje"),
    6: ("Plačila", "Pregled prejetih plačil in terjatev"),
    7: ("Analitika", "Poslovna poročila in kazalniki"),
    8: ("Nastavitve", "Podjetje, uporabniki in sistem"),
}


class TopToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TopToolbar")
        self.setFixedHeight(76)
        self.setStyleSheet("""
            QWidget#TopToolbar {
                background: transparent;
                border: none;
            }
            QLabel#ToolbarTitle {
                color: #0B1220;
                font-size: 21px;
                font-weight: 700;
            }
            QLabel#ToolbarSubtitle {
                color: #64748B;
                font-size: 9pt;
            }
            QFrame#SystemPill {
                background: #E8F8F5;
                border: 1px solid #C7EEE8;
                border-radius: 14px;
            }
            QLabel#SystemStatus {
                color: #0F766E;
                font-size: 9pt;
                font-weight: 700;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 12)
        layout.setSpacing(12)

        heading = QVBoxLayout()
        heading.setSpacing(1)
        self.title = QLabel()
        self.title.setObjectName("ToolbarTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("ToolbarSubtitle")
        heading.addWidget(self.title)
        heading.addWidget(self.subtitle)
        layout.addLayout(heading)
        layout.addStretch()

        pill = QFrame()
        pill.setObjectName("SystemPill")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(12, 6, 12, 6)
        pill_layout.setSpacing(7)
        status = QLabel("●  Sistem pripravljen")
        status.setObjectName("SystemStatus")
        status.setAlignment(Qt.AlignCenter)
        pill_layout.addWidget(status)
        layout.addWidget(pill)

        self.set_page(0)

    def set_page(self, index):
        title, subtitle = PAGE_META.get(index, ("JU-TAN Office", ""))
        self.title.setText(title)
        self.subtitle.setText(subtitle)
