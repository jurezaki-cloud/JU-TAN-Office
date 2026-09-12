from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class SidebarHeader(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SidebarHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(2)

        brand = QLabel("JU-TAN")
        brand.setObjectName("SidebarBrand")

        subtitle = QLabel("Office Enterprise")
        subtitle.setObjectName("SidebarSubtitle")

        line = QFrame()
        line.setObjectName("SidebarHeaderLine")
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(line)
