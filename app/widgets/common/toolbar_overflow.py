"""Reusable toolbar overflow (Več / •••) for dense action rows."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QPushButton, QSizePolicy, QWidget


class ToolbarOverflowButton(QPushButton):
    """Secondary-action overflow control with a themed popup menu."""

    def __init__(self, parent: QWidget | None = None, *, label: str = "Več") -> None:
        super().__init__(label, parent)
        self.setObjectName("SecondaryButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setToolTip("Več dejanj")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._menu = QMenu(self)
        self._menu.setObjectName("ToolbarOverflowMenu")
        self.setMenu(self._menu)

    @property
    def menu(self) -> QMenu:
        return self._menu

    def clear(self) -> None:
        self._menu.clear()

    def add_action(
        self,
        text: str,
        callback: Callable[[], None],
        *,
        icon: QIcon | None = None,
    ) -> QAction:
        action = self._menu.addAction(icon, text) if icon is not None else self._menu.addAction(text)
        action.triggered.connect(callback)
        return action

    def add_actions(
        self,
        entries: Iterable[tuple[str, Callable[[], None]] | tuple[str, Callable[[], None], QIcon]],
    ) -> list[QAction]:
        actions: list[QAction] = []
        for entry in entries:
            if len(entry) == 3:
                text, callback, icon = entry  # type: ignore[misc]
                actions.append(self.add_action(text, callback, icon=icon))
            else:
                text, callback = entry  # type: ignore[misc]
                actions.append(self.add_action(text, callback))
        return actions
