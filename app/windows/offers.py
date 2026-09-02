from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class Offers(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("📑 Ponudbe")
        title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        layout.addWidget(title)
        layout.addStretch()