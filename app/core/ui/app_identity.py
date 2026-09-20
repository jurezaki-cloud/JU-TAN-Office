"""Application identity — window icon, display name, Windows title-bar theme."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QWidget

from app.core.constants import APP_NAME, RESOURCE_DIR
from app.theme.colors import ThemeMode

_ICON_CACHE: QIcon | None = None


def resolve_app_icon_path() -> Path | None:
    candidates = (
        RESOURCE_DIR / "app.ico",
        RESOURCE_DIR / "app.png",
        Path(__file__).resolve().parents[3] / "resources" / "app.ico",
    )
    for path in candidates:
        if path.exists():
            return path
    return None


def application_icon() -> QIcon:
    global _ICON_CACHE
    if _ICON_CACHE is not None and not _ICON_CACHE.isNull():
        return _ICON_CACHE
    path = resolve_app_icon_path()
    if path is None:
        _ICON_CACHE = QIcon()
        return _ICON_CACHE
    _ICON_CACHE = QIcon(str(path))
    return _ICON_CACHE


def apply_application_identity(app: QApplication) -> None:
    """Set display name + icon before any window is shown."""
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("JU-TAN Studio")
    icon = application_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)


def apply_window_icon(widget: QWidget) -> None:
    icon = application_icon()
    if not icon.isNull():
        widget.setWindowIcon(icon)


def apply_native_titlebar_theme(widget: QWidget, mode: ThemeMode | str) -> None:
    """Integrate Windows title bar with dark/light theme when safe."""
    dark = mode in (ThemeMode.DARK, "dark")
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
    except Exception:
        return
    try:
        import ctypes

        value = ctypes.c_int(1 if dark else 0)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (Win10 1903+)
        # 19 = older attribute used on some builds
        dwm = ctypes.windll.dwmapi
        for attr in (20, 19):
            try:
                dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), ctypes.sizeof(value))
                break
            except Exception:
                continue
    except Exception:
        pass


def sync_titlebar_for_app(mode: ThemeMode | str) -> None:
    app = QApplication.instance() or QGuiApplication.instance()
    if app is None:
        return
    for widget in app.topLevelWidgets():
        if widget.isWindow():
            apply_native_titlebar_theme(widget, mode)
