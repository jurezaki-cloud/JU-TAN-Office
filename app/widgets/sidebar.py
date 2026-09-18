from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, Signal


class Sidebar(QWidget):

    page_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self.setFixedWidth(230)
        self.setObjectName("Sidebar")
        self.setStyleSheet("""
            QWidget#Sidebar { background:#101A2E; }
            QWidget#Sidebar QLabel { color:white; }
            QWidget#Sidebar QPushButton { background:transparent; color:#CAD5E3; border:none; border-radius:9px; padding:10px 14px; text-align:left; }
            QWidget#Sidebar QPushButton:hover { background:#172844; color:white; }
            QWidget#Sidebar QPushButton:focus { background:#17344A; color:#5EEADF; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("JU-TAN\nOFFICE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:21px;
            font-weight:bold;
            color:#5EEADF;
            padding:18px 10px;
        """)

        layout.addWidget(title)

        self.buttons = {}

        pages = [
            ("🏠 Dashboard", 0),
            ("📄 Računi", 1),
            ("👥 Stranke", 2),
            ("📑 Ponudbe", 3),
            ("🛠️ Storitve", 4),
            ("📦 Artikli", 5),
            ("💳 Plačila", 6),
            ("📊 Analitika", 7),
            ("⚙️ Nastavitve", 8),
        ]

        for text, index in pages:
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.setCursor(Qt.PointingHandCursor)

            button.clicked.connect(
                lambda checked=False, i=index: self.page_changed.emit(i)
            )

            layout.addWidget(button)

            self.buttons[index] = button

        layout.addStretch()
