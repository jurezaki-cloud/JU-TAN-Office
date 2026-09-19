from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class NavButton(QPushButton):
    def __init__(self, text, index):
        super().__init__(text)
        self.index = index
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setProperty("nav", True)


class Sidebar(QWidget):
    page_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(248)
        self.setObjectName("Sidebar")

        self.setStyleSheet("""
            QWidget#Sidebar {
                background: #0F1B2D;
                border-right: 1px solid #172A45;
            }
            QWidget#Sidebar QLabel { color: white; }
            QLabel#BrandMark {
                color: #19D3C5;
                font-size: 20px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#BrandCaption {
                color: #8FA4BD;
                font-size: 9px;
                font-weight: 600;
            }
            QLabel#SectionLabel {
                color: #70869F;
                font-size: 9px;
                font-weight: 700;
                padding: 8px 10px 2px 10px;
            }
            QPushButton[nav="true"] {
                background: transparent;
                color: #B9C7D8;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                text-align: left;
                font-weight: 600;
            }
            QPushButton[nav="true"]:hover {
                background: #172A45;
                color: white;
            }
            QPushButton[nav="true"]:checked {
                background: #123A4A;
                color: #5EEADF;
                border-left: 3px solid #19D3C5;
                padding-left: 11px;
            }
            QFrame#SidebarDivider {
                background: #22324A;
                max-height: 1px;
            }
            QLabel#VersionLabel {
                color: #60758E;
                font-size: 9px;
                padding: 4px 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(5)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(8, 2, 8, 16)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)

        brand = QLabel("JU-TAN")
        brand.setObjectName("BrandMark")
        caption = QLabel("OFFICE")
        caption.setObjectName("BrandCaption")
        brand_text.addWidget(brand)
        brand_text.addWidget(caption)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        self.buttons = {}

        layout.addWidget(self._section("PREGLED"))
        self._add_nav(layout, "Dashboard", 0)

        layout.addWidget(self._section("POSLOVANJE"))
        self._add_nav(layout, "Računi", 1)
        self._add_nav(layout, "Stranke", 2)
        self._add_nav(layout, "Ponudbe", 3)
        self._add_nav(layout, "Storitve", 4)
        self._add_nav(layout, "Artikli", 5)
        self._add_nav(layout, "Plačila", 6)

        layout.addWidget(self._section("POROČILA"))
        self._add_nav(layout, "Analitika", 7)

        layout.addStretch()

        divider = QFrame()
        divider.setObjectName("SidebarDivider")
        layout.addWidget(divider)

        self._add_nav(layout, "Nastavitve", 8)

        version = QLabel("JU-TAN Office  •  Enterprise")
        version.setObjectName("VersionLabel")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self.set_active(0)

    def _section(self, text):
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _add_nav(self, layout, text, index):
        button = NavButton(text, index)
        button.clicked.connect(
            lambda checked=False, i=index: self._navigate(i)
        )
        layout.addWidget(button)
        self.buttons[index] = button

    def _navigate(self, index):
        self.set_active(index)
        self.page_changed.emit(index)

    def set_active(self, index):
        button = self.buttons.get(index)
        if button is not None:
            button.setChecked(True)
