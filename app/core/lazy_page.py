"""Lazy nalaganje strani v QStackedWidget brez premika indeksov."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.core.errors import handle_error


class LazyPage(QWidget):
    """Ovojnica, ki ustvari pravo stran ob prvem prikazu ali klicu."""

    def __init__(self, factory: Callable[[], QWidget], placeholder: str = "") -> None:
        super().__init__()
        self._factory = factory
        self._inner: QWidget | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._hint = QLabel(placeholder)
        self._hint.setObjectName("KpiHint")
        self._hint.hide()
        layout.addWidget(self._hint)
        self._layout = layout

    def ensure(self) -> QWidget:
        if self._inner is None:
            try:
                self._inner = self._factory()
                self._hint.hide()
                self._layout.addWidget(self._inner, 1)
            except Exception as exc:
                handle_error(exc, context="lazy-page", parent=self)
                raise
        return self._inner

    def refresh(self) -> None:
        inner = self.ensure()
        method = getattr(inner, "refresh", None)
        if callable(method):
            method()

    @property
    def search(self):
        return getattr(self.ensure(), "search", None)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.ensure(), name)
