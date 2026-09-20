"""Centralni obravnavnik napak in prijazna sporočila uporabniku."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.logger import log_exception, logger

FRIENDLY = {
    "IntegrityError": "Zapis je povezan z drugimi podatki in ga ni mogoče izbrisati.",
    "ValueError": "Vneseni podatki niso veljavni.",
    "PermissionError": "Ni dovoljenja za to dejanje ali datoteko.",
    "FileNotFoundError": "Datoteka ne obstaja.",
    "JSONDecodeError": "Nastavitve so poškodovane. Obnovljene so privzete vrednosti.",
}


def friendly_message(exc: BaseException) -> str:
    """Pretvori tehnično izjemo v sporočilo za uporabnika (brez traceback)."""
    name = type(exc).__name__
    text = str(exc).strip()
    if "Traceback" in text or 'File "' in text or ".py:" in text:
        return "Prišlo je do nepričakovane napake."
    if name in ("ValueError", "PermissionError") and text:
        return text
    if name in FRIENDLY:
        return FRIENDLY[name]
    return "Prišlo je do nepričakovane napake."


def handle_error(
    exc: BaseException,
    *,
    context: str = "",
    parent: Any = None,
    recover: Callable[[], None] | None = None,
) -> str:
    """Zabeleži napako, opcijsko obnovi stanje in vrni sporočilo."""
    log_exception(exc, context)
    message = friendly_message(exc)
    if recover is not None:
        try:
            recover()
            logger.info("Obnovitev po napaki uspešna%s", f" ({context})" if context else "")
        except Exception as recovery_error:
            log_exception(recovery_error, "recovery")
    if parent is not None:
        try:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(parent, "JU-TAN Office", message)
        except Exception:
            pass
    return message
