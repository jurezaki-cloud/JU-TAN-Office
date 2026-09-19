from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.constants import APP_NAME, APP_VERSION
from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.theme.tokens import SIDEBAR_WIDTH_COLLAPSED


class SidebarFooter(QWidget):
    collapse_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SidebarFooter")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._collapsed = False

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 8, 0, 0)
        self._root.setSpacing(4)

        self.user_label = QLabel()
        self.user_label.setObjectName("SidebarFooterUser")
        self.user_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.user_label.setWordWrap(True)

        self.edition = QLabel(APP_NAME)
        self.edition.setObjectName("SidebarFooterTitle")
        self.edition.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.edition.setWordWrap(True)

        self.version = QLabel(f"v{APP_VERSION}")
        self.version.setObjectName("SidebarFooterVersion")
        self.version.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        row = QHBoxLayout()
        row.setContentsMargins(0, 4, 0, 0)
        row.setSpacing(4)
        row.addWidget(self.version, 1)

        self.btn_collapse = QPushButton()
        self.btn_collapse.setObjectName("SidebarCollapseButton")
        self.btn_collapse.setCursor(Qt.PointingHandCursor)
        self.btn_collapse.setFixedSize(28, 28)
        self.btn_collapse.setToolTip("Strni stransko vrstico")
        self.btn_collapse.clicked.connect(self._toggle)
        row.addWidget(self.btn_collapse, 0, Qt.AlignRight)

        self._root.addWidget(self.user_label)
        self._root.addWidget(self.edition)
        self._root.addLayout(row)
        self.refresh()
        self._refresh_collapse_icon()

    def refresh(self) -> None:
        try:
            from app.core.session import session

            user = session.user or "Uporabnik"
            role = session.role or ""
            if role and role.casefold() != str(user).casefold():
                self.user_label.setText(f"{user}\n{role}")
            else:
                self.user_label.setText(str(user))
        except Exception:
            self.user_label.setText("Uporabnik")

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed)
        self.user_label.setVisible(not self._collapsed)
        self.edition.setVisible(not self._collapsed)
        self.version.setVisible(not self._collapsed)
        self._refresh_collapse_icon()
        if self._collapsed:
            self.btn_collapse.setToolTip("Razširi stransko vrstico")
            self.setFixedWidth(SIDEBAR_WIDTH_COLLAPSED - 24)
        else:
            self.btn_collapse.setToolTip("Strni stransko vrstico")
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)

    def _refresh_collapse_icon(self) -> None:
        color = semantic_color("SIDEBAR_MUTED", "#94A3B8")
        name = "expand" if self._collapsed else "collapse"
        self.btn_collapse.setIcon(brand_icon(name, color=color, size=14))

    def _toggle(self) -> None:
        self.collapse_toggled.emit(not self._collapsed)
