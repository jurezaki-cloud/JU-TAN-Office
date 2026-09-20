from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class AppearanceCard(QWidget):
    theme_changed = Signal(str)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Videz")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        card.body.addWidget(self._caption("Theme"))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)
        self.theme_group = QButtonGroup(self)
        self.radio_light = QRadioButton("Light")
        self.radio_dark = QRadioButton("Dark")
        self.radio_auto = QRadioButton("Auto")
        for radio, key in (
            (self.radio_light, "light"),
            (self.radio_dark, "dark"),
            (self.radio_auto, "auto"),
        ):
            radio.setProperty("value", key)
            self.theme_group.addButton(radio)
            theme_row.addWidget(radio)
        theme_row.addStretch()
        card.body.addLayout(theme_row)
        self.radio_light.setChecked(True)

        card.body.addWidget(self._caption("Accent"))
        accent_row = QHBoxLayout()
        accent_row.setSpacing(8)
        self.accent_group = QButtonGroup(self)
        self.accent_group.setExclusive(True)
        self.accent_buttons = {}
        for key, label in (("blue", "Blue"), ("green", "Green"), ("orange", "Orange")):
            button = QPushButton(label)
            button.setObjectName("AccentChip")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setProperty("value", key)
            self.accent_group.addButton(button)
            self.accent_buttons[key] = button
            accent_row.addWidget(button)
        accent_row.addStretch()
        card.body.addLayout(accent_row)
        self.accent_buttons["green"].setChecked(True)

        card.body.addWidget(self._caption("Font Size"))
        font_row = QHBoxLayout()
        font_row.setSpacing(16)
        self.font_group = QButtonGroup(self)
        self.radio_font_small = QRadioButton("Small")
        self.radio_font_normal = QRadioButton("Normal")
        self.radio_font_large = QRadioButton("Large")
        for radio, key in (
            (self.radio_font_small, "small"),
            (self.radio_font_normal, "normal"),
            (self.radio_font_large, "large"),
        ):
            radio.setProperty("value", key)
            self.font_group.addButton(radio)
            font_row.addWidget(radio)
        font_row.addStretch()
        card.body.addLayout(font_row)
        self.radio_font_normal.setChecked(True)

        card.body.addWidget(self._caption("Corner Radius"))
        radius_row = QHBoxLayout()
        radius_row.setSpacing(16)
        self.radius_group = QButtonGroup(self)
        self.radio_radius_small = QRadioButton("Small")
        self.radio_radius_medium = QRadioButton("Medium")
        self.radio_radius_large = QRadioButton("Large")
        for radio, key in (
            (self.radio_radius_small, "small"),
            (self.radio_radius_medium, "medium"),
            (self.radio_radius_large, "large"),
        ):
            radio.setProperty("value", key)
            self.radius_group.addButton(radio)
            radius_row.addWidget(radio)
        radius_row.addStretch()
        card.body.addLayout(radius_row)
        self.radio_radius_medium.setChecked(True)

        layout.addWidget(card)

        self.theme_group.buttonClicked.connect(self._emit_theme)
        self.accent_group.buttonClicked.connect(self._emit_changed)
        self.font_group.buttonClicked.connect(self._emit_changed)
        self.radius_group.buttonClicked.connect(self._emit_changed)

    def values(self) -> dict:
        return {
            "theme": self._checked(self.theme_group, "light"),
            "accent": self._checked(self.accent_group, "blue"),
            "font_size": self._checked(self.font_group, "normal"),
            "radius": self._checked(self.radius_group, "medium"),
        }

    def set_values(self, appearance: dict) -> None:
        theme = appearance.get("theme", "light")
        {"light": self.radio_light, "dark": self.radio_dark, "auto": self.radio_auto}.get(
            theme, self.radio_light
        ).setChecked(True)
        accent = appearance.get("accent", "blue")
        if accent in self.accent_buttons:
            self.accent_buttons[accent].setChecked(True)
        font = appearance.get("font_size", "normal")
        {
            "small": self.radio_font_small,
            "normal": self.radio_font_normal,
            "large": self.radio_font_large,
        }.get(font, self.radio_font_normal).setChecked(True)
        radius = appearance.get("radius", "medium")
        {
            "small": self.radio_radius_small,
            "medium": self.radio_radius_medium,
            "large": self.radio_radius_large,
        }.get(radius, self.radio_radius_medium).setChecked(True)

    def _emit_theme(self, *_args):
        self.theme_changed.emit(self.values()["theme"])
        self.changed.emit()

    def _emit_changed(self, *_args):
        self.changed.emit()

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("DashboardMuted")
        return label

    @staticmethod
    def _checked(group: QButtonGroup, fallback: str) -> str:
        button = group.checkedButton()
        if button is None:
            return fallback
        return button.property("value") or fallback
