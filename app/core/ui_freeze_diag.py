"""Temporary UI-thread ENTER/EXIT diagnostics for freeze investigation.

Enable with env JU_TAN_FREEZE_DIAG=1. Logs to logger + optional file.
Safe to leave imported; no-ops when disabled.
"""

from __future__ import annotations

import functools
import os
import threading
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Iterator

_ENABLED = os.environ.get("JU_TAN_FREEZE_DIAG", "").strip() in {"1", "true", "yes"}
_DEPTH = 0
_LOCK = threading.Lock()
_FILE = None


def enabled() -> bool:
    return _ENABLED


def _log(msg: str) -> None:
    if not _ENABLED:
        return
    line = f"{time.strftime('%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d} | UI-DIAG | {msg}"
    try:
        from app.core.logger import logger

        logger.info("%s", line)
    except Exception:
        pass
    global _FILE
    try:
        if _FILE is None:
            from app.core.constants import LOG_DIR

            path = LOG_DIR / "ui_freeze_diag.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            _FILE = open(path, "a", encoding="utf-8")
        _FILE.write(line + "\n")
        _FILE.flush()
    except Exception:
        pass


@contextmanager
def span(name: str, **extra: Any) -> Iterator[None]:
    global _DEPTH
    if not _ENABLED:
        yield
        return
    suffix = ""
    if extra:
        suffix = " " + " ".join(f"{k}={v!r}" for k, v in extra.items())
    with _LOCK:
        pad = "  " * _DEPTH
        _DEPTH += 1
    _log(f"{pad}ENTER {name}{suffix}")
    t0 = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - t0) * 1000
        with _LOCK:
            _DEPTH = max(0, _DEPTH - 1)
            pad = "  " * _DEPTH
        _log(f"{pad}EXIT  {name} elapsed_ms={ms:.1f}{suffix}")


def timed(name: str | None = None) -> Callable:
    def deco(fn: Callable) -> Callable:
        label = name or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with span(label):
                return fn(*args, **kwargs)

        return wrapper

    return deco


def install_faulthandler_watchdog(interval_sec: float = 5.0) -> None:
    """Dump all Python stacks periodically — use only while reproducing freezes."""
    if not _ENABLED:
        return
    import faulthandler
    import sys

    faulthandler.enable(file=sys.stderr, all_threads=True)
    try:
        from app.core.constants import LOG_DIR

        dump_path = LOG_DIR / "ui_freeze_stacks.log"
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_file = open(dump_path, "a", encoding="utf-8")
        faulthandler.dump_traceback_later(
            interval_sec, repeat=True, file=dump_file, exit=False
        )
        _log(f"faulthandler watchdog armed interval={interval_sec}s -> {dump_path}")
    except Exception as exc:
        _log(f"faulthandler arm failed: {exc}")


def wrap_qfont_set_point_size() -> None:
    """Capture stack when QFont.setPointSize receives <= 0."""
    if not _ENABLED:
        return
    try:
        from PySide6.QtGui import QFont
    except Exception:
        return
    original = QFont.setPointSize

    def patched(self, size):  # noqa: ANN001
        if size is None or int(size) <= 0:
            stack = "".join(traceback.format_stack(limit=25))
            _log(f"QFont.setPointSize({size!r}) CALLER STACK:\n{stack}")
        return original(self, size)

    QFont.setPointSize = patched  # type: ignore[method-assign]
    _log("QFont.setPointSize wrapper installed")
