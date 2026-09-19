"""Reusable page chrome — header, toolbar strip, empty state."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.brand_icons import brand_icon
from app.theme.tokens import SPACE_2, SPACE_4
from app.widgets.cards.enterprise_card import EnterpriseCard


class PageHeader(QWidget):
    """Title + optional description + optional primary action."""

    action_clicked = Signal()

    def __init__(
        self,
        title: str = "",
        description: str = "",
        *,
        action_text: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("PageHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, SPACE_2)
        layout.setSpacing(SPACE_4)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("PageHeaderTitle")
        self.description = QLabel(description)
        self.description.setObjectName("PageHeaderDescription")
        self.description.setVisible(bool(description))
        text.addWidget(self.title)
        text.addWidget(self.description)
        layout.addLayout(text, 1)

        self.action: QPushButton | None = None
        if action_text:
            self.action = QPushButton(action_text)
            self.action.setObjectName("PrimaryButton")
            self.action.setCursor(Qt.PointingHandCursor)
            self.action.setMinimumHeight(36)
            self.action.setIcon(brand_icon("new", color="#FFFFFF", size=16))
            self.action.clicked.connect(self.action_clicked.emit)
            layout.addWidget(self.action, 0, Qt.AlignTop)

    def set_texts(self, title: str, description: str = "") -> None:
        self.title.setText(title)
        self.description.setText(description)
        self.description.setVisible(bool(description))


class PageToolbar(QWidget):
    """Search / filters / secondary actions row."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PageToolbar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, SPACE_2)
        self.layout.setSpacing(SPACE_2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_stretch(self) -> None:
        self.layout.addStretch(1)


class EmptyState(EnterpriseCard):
    """Intentional empty module state with optional CTA."""

    action_clicked = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        parent=None,
        action_text: str = "Dodaj prvi zapis",
        *,
        show_action: bool = True,
    ):
        super().__init__("EmptyStateCard", parent)
        self.setMinimumHeight(220)

        self.title = QLabel(title)
        self.title.setObjectName("EmptyStateTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("EmptyStateSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)

        self.action = QPushButton(action_text)
        self.action.setObjectName("PrimaryButton")
        self.action.setCursor(Qt.PointingHandCursor)
        self.action.setMinimumHeight(36)
        self.action.setIcon(brand_icon("new", color="#FFFFFF", size=16))
        self.action.clicked.connect(self.action_clicked.emit)
        self.action.setVisible(show_action)

        self.body.addStretch()
        self.body.addWidget(self.title)
        self.body.addWidget(self.subtitle)
        self.body.addWidget(self.action, 0, Qt.AlignHCenter)
        self.body.addStretch()

    def set_message(self, title: str, subtitle: str, show_action: bool | None = None) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)
        if show_action is None:
            show_action = "zadetkov" not in (title or "").casefold()
        self.action.setVisible(show_action)
