import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
)

from app.widgets.sidebar import Sidebar
from app.widgets.toolbar import TopToolbar
from app.widgets.statusbar import StatusBar

from app.windows.dashboard import Dashboard

from app.modules.customers import CustomerPage
from app.modules.articles import ArticlePage


class EmptyPage(QWidget):

    def __init__(self, title):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(title)
        label.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        layout.addWidget(label)
        layout.addStretch()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("JU-TAN Office Enterprise")
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        # Desni del
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(15, 15, 15, 15)

        self.toolbar = TopToolbar()
        right_layout.addWidget(self.toolbar)

        # Strani
        self.stack = QStackedWidget()

        self.dashboard = Dashboard()
        self.customers = CustomerPage()
        self.articles = ArticlePage()

        self.stack.addWidget(self.dashboard)                 # 0
        self.stack.addWidget(EmptyPage("Računi"))            # 1
        self.stack.addWidget(self.customers)                 # 2
        self.stack.addWidget(EmptyPage("Ponudbe"))           # 3
        self.stack.addWidget(EmptyPage("Storitve"))          # 4
        self.stack.addWidget(self.articles)                  # 5
        self.stack.addWidget(EmptyPage("Plačila"))           # 6
        self.stack.addWidget(EmptyPage("Analitika"))         # 7
        self.stack.addWidget(EmptyPage("Nastavitve"))        # 8

        right_layout.addWidget(self.stack)

        root_layout.addWidget(right)

        self.setStatusBar(StatusBar())

        self.sidebar.page_changed.connect(self.change_page)

    def change_page(self, index):

        if index == 2:
            self.customers.refresh()

        elif index == 5:
            self.articles.refresh()

        self.stack.setCurrentIndex(index)


def run():

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())