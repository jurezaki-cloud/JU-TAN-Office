"""Settings Center section chrome — title + muted caption."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.theme.tokens import SPACE_1, SPACE_2, SPACE_3


class SettingsSectionHeader(QWidget):
    """Category divider used inside the settings content grid."""

    def __init__(self, title: str, caption: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsSectionHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, SPACE_3, 0, SPACE_1)
        root.setSpacing(SPACE_1)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE_2)

        self.title = QLabel(title)
        self.title.setObjectName("SettingsSectionTitle")
        row.addWidget(self.title)
        row.addStretch(1)
        root.addLayout(row)

        self.caption = QLabel(caption)
        self.caption.setObjectName("SettingsSectionCaption")
        self.caption.setWordWrap(True)
        self.caption.setVisible(bool(caption))
        root.addWidget(self.caption)

        rule = QFrame()
        rule.setObjectName("SettingsSectionRule")
        rule.setFixedHeight(1)
        rule.setFrameShape(QFrame.NoFrame)
        root.addWidget(rule)

    def set_texts(self, title: str, caption: str = "") -> None:
        self.title.setText(title)
        self.caption.setText(caption)
        self.caption.setVisible(bool(caption))
