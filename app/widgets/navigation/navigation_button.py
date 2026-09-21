from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QSizePolicy

from app.theme.colors import semantic_color
from app.theme.tokens import ICON_SIZE_MD, NAV_ITEM_HEIGHT


class NavigationButton(QPushButton):
    clicked_index = Signal(int)

    def __init__(
        self,
        text: str,
        index: int,
        icon: QIcon | str | Path | None = None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.index = index
        self._collapsed = False
        self._full_text = text
        self._icon_name: str | None = None

        self.setObjectName("NavigationButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setAutoExclusive(False)
        self.setFixedHeight(NAV_ITEM_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip(text)
        # Let QSS alone drive hover/checked paint — custom overlays + effects flicker.
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAutoFillBackground(False)

        self.set_navigation_icon(icon)
        self.clicked.connect(self._emit_index)
        self.toggled.connect(self._on_toggled)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = bool(collapsed)
        if self._collapsed:
            self.setText("")
            self.setToolTip(self._full_text)
        else:
            self.setText(self._full_text)
            self.setToolTip(self._full_text)

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name

    def set_navigation_icon(self, icon: QIcon | str | Path | None) -> None:
        if icon is None:
            return

        if isinstance(icon, (str, Path)):
            path = Path(icon)
            if not path.exists():
                return
            qicon = QIcon(str(path))
        else:
            qicon = icon

        if qicon.isNull():
            return

        self.setIcon(qicon)
        self.setIconSize(QSize(ICON_SIZE_MD, ICON_SIZE_MD))

    def refresh_active_icon(self) -> None:
        """Accent icon when selected; muted otherwise.

        Collapsed selected uses sidebar text color so the left rail alone
        carries selection weight (matches expanded visual balance).
        """
        if not self._icon_name:
            return
        from app.core.ui.brand_icons import brand_icon

        if self.isChecked() and not self._collapsed:
            color = semantic_color("PRIMARY", "#059669")
        else:
            color = semantic_color("SIDEBAR_TEXT", "#F8FAFC")
        self.set_navigation_icon(brand_icon(self._icon_name, color=color, size=ICON_SIZE_MD))

    def _on_toggled(self, _checked: bool) -> None:
        self.refresh_active_icon()

    def _emit_index(self):
        self.clicked_index.emit(self.index)
