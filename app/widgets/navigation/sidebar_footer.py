from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SidebarFooter(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SidebarFooter")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        edition = QLabel("Enterprise Edition")
        edition.setObjectName("SidebarFooterTitle")
        edition.setAlignment(Qt.AlignCenter)

        version = QLabel("v2.0")
        version.setObjectName("SidebarFooterVersion")
        version.setAlignment(Qt.AlignCenter)

        layout.addWidget(edition)
        layout.addWidget(version)
