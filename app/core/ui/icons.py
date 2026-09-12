"""Enotne ikone iz QStyle — toolbar, meni, dialogi, gumbi."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QPushButton, QStyle

_KEYS = {
    "new": QStyle.SP_FileDialogNewFolder,
    "save": QStyle.SP_DialogSaveButton,
    "search": QStyle.SP_FileDialogContentsView,
    "print": QStyle.SP_FileDialogDetailedView,
    "export": QStyle.SP_ArrowDown,
    "refresh": QStyle.SP_BrowserReload,
    "close": QStyle.SP_DialogCloseButton,
    "copy": QStyle.SP_DialogResetButton,
    "edit": QStyle.SP_FileDialogContentsView,
    "delete": QStyle.SP_TrashIcon,
    "open": QStyle.SP_DialogOpenButton,
    "apply": QStyle.SP_DialogApplyButton,
    "info": QStyle.SP_MessageBoxInformation,
    "warning": QStyle.SP_MessageBoxWarning,
    "ok": QStyle.SP_DialogOkButton,
    "cancel": QStyle.SP_DialogCancelButton,
}


_ICON_CACHE: dict[str, QIcon] = {}


def standard_icon(name: str) -> QIcon:
    cached = _ICON_CACHE.get(name)
    if cached is not None and not cached.isNull():
        return cached
    app = QApplication.instance()
    if app is None:
        return QIcon()
    style = app.style()
    key = _KEYS.get(name, QStyle.SP_FileIcon)
    icon = style.standardIcon(key)
    _ICON_CACHE[name] = icon
    return icon


def apply_button_icon(button: QPushButton, name: str) -> None:
    icon = standard_icon(name)
    if not icon.isNull():
        button.setIcon(icon)
