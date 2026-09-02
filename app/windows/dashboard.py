from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)


class StatCard(QFrame):
    def __init__(self, title, value):
        super().__init__()

        self.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #dddddd;
                border-radius:12px;
            }
        """)

        layout = QVBoxLayout(self)

        titleLabel = QLabel(title)
        titleLabel.setStyleSheet("font-size:14px;color:gray;")

        valueLabel = QLabel(value)
        valueLabel.setStyleSheet("""
            font-size:26px;
            font-weight:bold;
        """)

        layout.addWidget(titleLabel)
        layout.addWidget(valueLabel)


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        naslov = QLabel("Dashboard")
        naslov.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        layout.addWidget(naslov)

        cards = QHBoxLayout()

        cards.addWidget(StatCard("Prihodki", "0 €"))
        cards.addWidget(StatCard("Računi", "0"))
        cards.addWidget(StatCard("Stranke", "0"))
        cards.addWidget(StatCard("Ponudbe", "0"))

        layout.addLayout(cards)

        graf = QFrame()
        graf.setMinimumHeight(350)
        graf.setStyleSheet("""
            background:white;
            border:1px solid #dddddd;
            border-radius:12px;
        """)

        g = QVBoxLayout(graf)

        txt = QLabel("Graf poslovanja (v naslednji verziji)")
        txt.setStyleSheet("""
            font-size:18px;
            color:gray;
        """)

        g.addWidget(txt)

        layout.addWidget(graf)