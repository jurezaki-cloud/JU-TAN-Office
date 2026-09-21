"""Application startup licensing gate."""
from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtWidgets import QMessageBox

from app.services.licensing_service import LicenseError, LicenseState, validate
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

    try:
        result = validate(state)
        if result.get("status") == "active":
            # Persist refreshed server metadata/token when supplied.
            state.apply_server_result(result)
            state.save()
            return True
        QMessageBox.critical(parent, "Licenca", "Licenca JU-TAN Office ni aktivna.")
        return False
    except LicenseError as exc:
        if _grace_valid(state.grace_until):
            return True
        QMessageBox.critical(parent, "Licenca", str(exc))
        return False
