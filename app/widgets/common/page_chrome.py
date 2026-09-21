"""Reusable page chrome — header, toolbar strip, empty state.

Enterprise title hierarchy (Phase 4.2):
- Shell ``ToolbarTitle`` owns the module name (authoritative H1).
- ``PageHeader`` is optional content chrome: lead description + primary action.
  Titles are hidden by default so they never duplicate the shell.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.brand_icons import brand_icon
from app.theme.tokens import SPACE_2, SPACE_3, SPACE_4, SPACE_5
from app.widgets.cards.enterprise_card import EnterpriseCard


class PageHeader(QWidget):
    """Optional page lead: description + primary action (no duplicate H1)."""

    action_clicked = Signal()

    def __init__(
        self,
        title: str = "",
        description: str = "",
        *,
        action_text: str | None = None,
        show_title: bool = False,
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
        self.title.setVisible(bool(title) and show_title)
        self.description = QLabel(description)
        self.description.setObjectName("PageHeaderDescription")
        self.description.setWordWrap(True)
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

        self._show_title = show_title

    def set_texts(self, title: str, description: str = "") -> None:
        self.title.setText(title)
        self.title.setVisible(bool(title) and self._show_title)
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


class DocumentListToolbar(QFrame):
    """Elevated search / filter / actions strip for document list pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentListToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(SPACE_3, SPACE_2, SPACE_3, SPACE_2)
        self.layout.setSpacing(SPACE_2)

    def add_stretch(self) -> None:
        self.layout.addStretch(1)


class EmptyState(EnterpriseCard):
    """Module empty state — DashboardEmptyState typography + optional CTA."""

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
        self.title.setObjectName("DashboardEmptyState")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("DashboardEmptyState")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)

        self.action = QPushButton(action_text)
        self.action.setObjectName("PrimaryButton")
        self.action.setCursor(Qt.PointingHandCursor)
        self.action.setMinimumHeight(36)
        self.action.setIcon(brand_icon("new", color="#FFFFFF", size=16))
        self.action.clicked.connect(self.action_clicked.emit)
        self.action.setVisible(show_action)

        self.body.setContentsMargins(SPACE_4, SPACE_5, SPACE_4, SPACE_5)
        self.body.setSpacing(SPACE_2)
        self.body.addStretch()
        self.body.addWidget(self.title)
        self.body.addWidget(self.subtitle)
        self.body.addSpacing(SPACE_3)
        self.body.addWidget(self.action, 0, Qt.AlignHCenter)
        self.body.addStretch()

    def set_message(self, title: str, subtitle: str, show_action: bool | None = None) -> None:
        self.title.setText(title)
        self.subtitle.setText(subtitle)
        if show_action is None:
            show_action = "zadetkov" not in (title or "").casefold()
        self.action.setVisible(show_action)
