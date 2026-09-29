"""Settings Center left navigation — category rail."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.theme.tokens import ICON_SIZE_SM, SPACE_1, SPACE_2, SPACE_3, SPACE_4


# (key, label, icon_name, group_title or None for first item in group)
SETTINGS_NAV_ITEMS: list[tuple[str, str, str, str | None]] = [
    ("overview", "Pregled", "dashboard", "CENTER"),
    ("documents", "Dokumenti", "documents", "KONFIGURACIJA"),
    ("appearance", "Videz", "settings", None),
    ("modules", "Moduli", "travel", None),
    ("security", "Varnost", "lock", "DOSTOP"),
    ("users", "Uporabniki", "user", None),
    ("backup", "Varnostne kopije", "export", "SISTEM"),
    ("license", "Licenca", "company", None),
    ("updates", "Posodobitve", "refresh", None),
    ("privacy", "Zasebnost", "lock", None),
    ("about", "O aplikaciji", "analytics", None),
    ("danger", "Nevarno območje", "delete", None),
]


class SettingsNav(QFrame):
    """Vertical category list for the Settings Center."""

    category_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsNav")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_3, SPACE_4, SPACE_3, SPACE_4)
        layout.setSpacing(SPACE_1)

        eyebrow = QLabel("NASTAVITVE")
        eyebrow.setObjectName("SettingsNavEyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("Settings Center")
        title.setObjectName("SettingsNavTitle")
        layout.addWidget(title)

        hint = QLabel("Kategorije sistema")
        hint.setObjectName("SettingsNavHint")
        layout.addWidget(hint)
        layout.addSpacing(SPACE_3)

        # Scrollable: at 125-150 % scaling a maximised window is shorter than the list.
        self._scroll = QScrollArea()
        self._scroll.setObjectName("SettingsNavScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Not a tab stop: Tab moves between the category buttons and scrolls to them.
        self._scroll.setFocusPolicy(Qt.NoFocus)
        items = QWidget()
        items.setObjectName("SettingsNavList")
        items_layout = QVBoxLayout(items)
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(SPACE_1)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        self._group_labels: dict[str, QLabel] = {}

        for key, label, icon_name, group_title in SETTINGS_NAV_ITEMS:
            if group_title:
                section = QLabel(group_title)
                section.setObjectName("SettingsNavGroup")
                items_layout.addSpacing(SPACE_2)
                items_layout.addWidget(section)
                self._group_labels[key] = section

            button = QPushButton(label)
            button.setObjectName("SettingsNavItem")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(28)
            button.setProperty("category", key)
            button.setIcon(
                brand_icon(icon_name, color=semantic_color("TEXT_MUTED", "#64748B"), size=ICON_SIZE_SM)
            )
            button.clicked.connect(lambda _checked=False, k=key: self._select(k))
            self._group.addButton(button)
            self._buttons[key] = button
            items_layout.addWidget(button)

        items_layout.addStretch(1)
        self._scroll.setWidget(items)
        layout.addWidget(self._scroll, 1)
        self._active = "overview"
        self._buttons["overview"].setChecked(True)
        self._refresh_icons()

    def select(self, key: str) -> None:
        if key not in self._buttons:
            return
        self._select(key, emit=False)

    def set_category_visible(self, key: str, visible: bool) -> None:
        button = self._buttons.get(key)
        if button is not None:
            button.setVisible(visible)
        label = self._group_labels.get(key)
        if label is not None:
            label.setVisible(visible)

    def _select(self, key: str, *, emit: bool = True) -> None:
        button = self._buttons.get(key)
        if button is None:
            return
        button.setChecked(True)
        self._active = key
        self._refresh_icons()
        # Also runs for the page's scroll-spy, so the highlighted category stays in view.
        self._scroll.ensureWidgetVisible(button, 0, button.height())
        if emit:
            self.category_selected.emit(key)

    def _refresh_icons(self) -> None:
        for key, label, icon_name, _group in SETTINGS_NAV_ITEMS:
            button = self._buttons[key]
            if button.isChecked():
                color = semantic_color("PRIMARY", "#059669")
            else:
                color = semantic_color("TEXT_MUTED", "#64748B")
            button.setIcon(brand_icon(icon_name, color=color, size=ICON_SIZE_SM))
