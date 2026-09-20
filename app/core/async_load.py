"""Odloženo nalaganje UI seznamov (naslednji event-loop tick)."""

from __future__ import annotations

from collections.abc import Callable


def defer(callback: Callable[[], None]) -> None:
    """Zaženi callback asinhrono v Qt zanki, če je na voljo."""
    try:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, callback)
    except Exception:
        callback()
