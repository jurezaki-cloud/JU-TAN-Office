from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QToolButton, QWidget, QHBoxLayout


class ToolbarUser(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarUser")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.button = QToolButton()
        self.button.setObjectName("ToolbarUserButton")
        self.button.setText("Administrator")
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.button.setFixedHeight(36)
        self.button.setCursor(Qt.PointingHandCursor)

        menu = QMenu(self.button)
        profile = menu.addAction("Administrator")
        profile.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Uporabniški profil")
        self.button.setMenu(menu)

        layout.addWidget(self.button)
