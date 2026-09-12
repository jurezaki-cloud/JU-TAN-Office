"""Odloži iskanje, da tipkanje ne sproži poizvedbe ob vsakem znaku."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer


class Debouncer(QObject):
    def __init__(self, callback: Callable[..., None], ms: int = 180, parent=None) -> None:
        super().__init__(parent)
        self._callback = callback
        self._args: tuple = ()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(ms)
        self._timer.timeout.connect(self._fire)

    def __call__(self, *args) -> None:
        self._args = args
        self._timer.start()

    def flush(self) -> None:
        self._timer.stop()
        self._fire()

    def _fire(self) -> None:
        self._callback(*self._args)
