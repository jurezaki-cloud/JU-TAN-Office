"""Ozadna opravila za PDF, Excel in tisk."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


def run_in_thread(
    work: Callable[[], Any],
    *,
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[BaseException], None] | None = None,
) -> threading.Thread:
    def runner() -> None:
        try:
            result = work()
        except BaseException as exc:
            if on_error is not None:
                _to_ui(lambda: on_error(exc))
            return
        if on_done is not None:
            _to_ui(lambda: on_done(result))

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return thread


def _to_ui(callback: Callable[[], None]) -> None:
    try:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, callback)
    except Exception:
        callback()
