"""Process-lifetime Windows mutex for Inno Setup AppMutex (upgrade safety)."""

from __future__ import annotations

import sys
from typing import Any

# Must match packaging/installer.iss AppMutex=
APP_MUTEX_NAME = "JU-TANOfficeMutex"

_mutex_handle: Any = None


def acquire_app_mutex() -> None:
    """Create (and hold) the named mutex used by the installer AppMutex directive.

    Does not enforce single-instance UI behaviour — only keeps the mutex alive
    so Inno Setup can wait for a clean exit during upgrades.
    """
    global _mutex_handle
    if sys.platform != "win32":
        return
    if _mutex_handle is not None:
        return

    import ctypes

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    handle = kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
    if handle:
        _mutex_handle = handle
