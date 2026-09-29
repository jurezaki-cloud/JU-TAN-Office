"""Enotne ikone — brand stroke set with QStyle fallback."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QPushButton, QStyle

from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color

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

_BRAND_ALIAS = {
    "new": "new",
    "save": "save",
    "search": "search",
    "print": "print",
    "export": "export",
    "refresh": "refresh",
    "edit": "edit",
    "delete": "delete",
    "pdf": "pdf",
    "lock": "lock",
    "filter": "filter",
    "calendar": "calendar",
    "more": "more",
    "settings": "settings",
}


_ICON_CACHE: dict[str, QIcon] = {}

# Button properties set by apply_button_icon(), read back by refresh_button_icons().
_ICON_NAME_PROPERTY = "juTanIconName"
_ICON_KEY_PROPERTY = "juTanIconKey"


def standard_icon(name: str, *, color: str | None = None) -> QIcon:
    brand_name = _BRAND_ALIAS.get(name, name)
    try:
        icon = brand_icon(
            brand_name,
            color=color or semantic_color("TEXT", "#0F172A"),
            size=16,
        )
        if not icon.isNull():
            return icon
    except Exception:
        pass
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
    """Apply a brand icon whose color matches the button variant fill."""
    object_name = button.objectName() or ""
    if object_name in {"PrimaryButton", "SuccessButton"}:
        color = "#FFFFFF"
    elif object_name == "DangerButton":
        # Danger is outline-by-default — use the danger stroke, not white-on-transparent.
        color = semantic_color("DANGER", "#DC2626")
    else:
        color = semantic_color("TEXT", "#0F172A")
    icon = standard_icon(name, color=color)
    if not icon.isNull():
        button.setIcon(icon)
        button.setProperty(_ICON_NAME_PROPERTY, name)
        button.setProperty(_ICON_KEY_PROPERTY, button.icon().cacheKey())


def refresh_button_icons() -> None:
    """Re-tint apply_button_icon() icons for the active theme.

    The colour is baked into the icon, so after a live theme switch the old theme's TEXT
    colour would sit on the new surface (white-on-white / black-on-black). Buttons whose
    icon was replaced by other code since then are left alone.
    """
    app = QApplication.instance()
    if app is None:
        return
    for widget in app.allWidgets():
        if not isinstance(widget, QPushButton):
            continue
        name = widget.property(_ICON_NAME_PROPERTY)
        if name and widget.icon().cacheKey() == widget.property(_ICON_KEY_PROPERTY):
            apply_button_icon(widget, name)
