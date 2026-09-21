"""Lazy nalaganje strani v QStackedWidget brez premika indeksov."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.core.errors import handle_error


class LazyPage(QWidget):
    """Ovojnica, ki ustvari pravo stran ob prvem prikazu ali klicu.

    Shell-first pages may set ``defers_initial_refresh = True`` and load data
    after first paint (e.g. via ``showEvent``). In that case ``refresh()`` is a
    no-op until the inner page marks ``_data_loaded``.
    """

    def __init__(self, factory: Callable[[], QWidget], placeholder: str = "") -> None:
        super().__init__()
        self._factory = factory
        self._placeholder = placeholder
        self._inner: QWidget | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._layout = layout

    @property
    def is_loaded(self) -> bool:
        return self._inner is not None

    def ensure(self) -> QWidget:
        """Build the inner page shell if needed (no data refresh)."""
        if self._inner is None:
            try:
                self._inner = self._factory()
                self._layout.addWidget(self._inner, 1)
            except Exception as exc:
                handle_error(exc, context="lazy-page", parent=self)
                raise
        return self._inner

    def refresh(self) -> None:
        inner = self.ensure()
        # Shell-first pages own their first deferred load after paint.
        if getattr(inner, "defers_initial_refresh", False) and not getattr(
            inner, "_data_loaded", False
        ):
            return
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
