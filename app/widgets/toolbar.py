from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class TopToolbar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 12)

        naslov = QLabel("Poslovni pregled")
        naslov.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
        """)

        uporabnik = QLabel("●  Sistem pripravljen")
        uporabnik.setStyleSheet("color:#0F766E;font-weight:600;background:#DDF8F4;padding:7px 12px;border-radius:12px;")

        layout.addWidget(naslov)

        layout.addStretch()

        layout.addWidget(uporabnik)
