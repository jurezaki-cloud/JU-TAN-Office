from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from app.widgets.navigation.navigation_button import NavigationButton
from app.widgets.navigation.sidebar_footer import SidebarFooter
from app.widgets.navigation.sidebar_header import SidebarHeader


class ModernSidebar(QWidget):

    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        layout.addWidget(SidebarHeader())

        nav = QWidget()
        nav.setObjectName("SidebarNav")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 8, 0, 8)
        nav_layout.setSpacing(6)

        self.buttons: dict[int, NavigationButton] = {}

        # Isti indeksi kot QStackedWidget v MainWindow.
        pages = [
            ("Dashboard", 0),
            ("Računi", 1),
            ("Ponudbe", 3),
            ("Naročila", 9),
            ("Stranke", 2),
            ("Artikli", 4),
            ("Skladišče", 10),
            ("Suppliers", 11),
            ("Purchase Orders", 12),
            ("Documents", 13),
            ("CRM", 14),
            ("Reports", 15),
            ("Automation", 16),
            ("Podjetje", 5),
            ("Plačila", 6),
            ("Analytics", 7),
            ("⚙ Nastavitve", 8),
        ]

        for text, index in pages:
            button = NavigationButton(text, index)
            button.clicked_index.connect(self._on_navigate)
            nav_layout.addWidget(button)
            self.buttons[index] = button

        scroll = QScrollArea()
        scroll.setObjectName("SidebarNavScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(nav)

        layout.addWidget(scroll, 1)
        layout.addWidget(SidebarFooter())

        self.set_active(0)

    def _on_navigate(self, index: int):
        self.set_active(index)
        self.page_changed.emit(index)

    def set_active(self, index: int):
        for button_index, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(button_index == index)
            button.blockSignals(False)
