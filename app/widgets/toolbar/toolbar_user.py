from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMenu, QToolButton, QWidget

from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color


class ToolbarUser(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarUser")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.button = QToolButton()
        self.button.setObjectName("ToolbarUserButton")
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.button.setFixedHeight(36)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setIcon(brand_icon("user", color=semantic_color("TEXT_MUTED", "#64748B"), size=16))

        self._menu = QMenu(self.button)
        self.button.setMenu(self._menu)
        layout.addWidget(self.button)
        self.refresh()

    def refresh(self) -> None:
        try:
            from app.core.session import session

            user = session.user or "Uporabnik"
            role = session.role or ""
        except Exception:
            user, role = "Uporabnik", ""
        label = user if not role else f"{user}"
        self.button.setText(label)
        self._menu.clear()
        profile = self._menu.addAction(user)
        profile.setEnabled(False)
        if role:
            role_action = self._menu.addAction(role)
            role_action.setEnabled(False)
        self._menu.addSeparator()
        self._menu.addAction("Uporabniški profil")
