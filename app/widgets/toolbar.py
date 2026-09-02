from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class TopToolbar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        naslov = QLabel("JU-TAN Office Enterprise")
        naslov.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        uporabnik = QLabel("👤 Administrator")

        layout.addWidget(naslov)

        layout.addStretch()

        layout.addWidget(uporabnik)