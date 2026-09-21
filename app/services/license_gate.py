"""Application startup licensing gate."""
from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtWidgets import QMessageBox

from app.services.licensing_service import (
    LicenseError,
    LicenseState,
    clear_license_state,
    device_bound,
    validate,
)
from app.windows.license_activation import LicenseActivationDialog


def _grace_valid(value: str) -> bool:
    if not value:
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt >= datetime.now(timezone.utc)
    except ValueError:
        return False


def ensure_licensed(parent=None) -> bool:
    state = LicenseState.load()
    if state is None:
        return LicenseActivationDialog(parent).exec() == LicenseActivationDialog.Accepted

    if not device_bound(state):
        clear_license_state()
        QMessageBox.critical(
            parent,
            "Licenca",
            "Licenca je vezana na drugo napravo.\n\n"
            "Lokalna aktivacija je bila odstranjena. Aktivirajte JU-TAN Office na tej napravi.",
        )
        return LicenseActivationDialog(parent).exec() == LicenseActivationDialog.Accepted

    try:
        result = validate(state)
        if result.get("status") == "active":
            state.apply_server_result(result)
            state.save()
            return True
        QMessageBox.critical(parent, "Licenca", "Licenca JU-TAN Office ni aktivna.")
        return False
    except LicenseError as exc:
        message = str(exc)
        if "ni veljavna za to napravo" in message.lower():
            clear_license_state()
            QMessageBox.critical(parent, "Licenca", message)
            return LicenseActivationDialog(parent).exec() == LicenseActivationDialog.Accepted
        if _grace_valid(state.grace_until):
            return True
        QMessageBox.critical(parent, "Licenca", message)
        return False
