"""Preverjanje sheme in prvega zagona."""

from __future__ import annotations

from app.core.constants import SCHEMA_VERSION
from app.core.logger import logger
from app.modules.settings.settings_controller import SettingsController, default_settings


def ensure_schema_version() -> int:
    controller = SettingsController()
    extras = controller.load_extras()
    current = int(extras.get("database_version") or 0)
    if current < SCHEMA_VERSION:
        from app.database.database import db
        from app.database.migrations import apply_pending_migrations

        with db.transaction() as conn:
            apply_pending_migrations(current, SCHEMA_VERSION, conn)
        extras["database_version"] = SCHEMA_VERSION
        controller.save_extras_unrestricted(extras)
        logger.info("Shema baze: %s", SCHEMA_VERSION)
    return int(extras.get("database_version") or SCHEMA_VERSION)


def needs_first_run() -> bool:
    extras = SettingsController().load_extras()
    if extras.get("setup_complete"):
        return False
    try:
        from app.database.company_repository import company_repository
        row = company_repository.get_company()
        name = (row[1] if row else "") or ""
        return not name.strip()
    except Exception:
        return True


def mark_setup_complete(*, administrator: str = "Administrator", currency: str = "EUR") -> None:
    controller = SettingsController()
    extras = controller.load_extras()
    extras["setup_complete"] = True
    extras["administrator"] = administrator
    extras["currency"] = currency
    extras["database_version"] = SCHEMA_VERSION
    controller.save_extras_unrestricted(extras)
