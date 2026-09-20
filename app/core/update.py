"""Nadgradnja: primerjava verzij, backup, rollback."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.core.constants import APP_VERSION, BACKUP_DIR, DATA_DIR, DATABASE_PATH
from app.core.logger import logger
from app.core.permissions import audit, require
from app.modules.settings.settings_controller import SettingsController

VERSION_MARK = DATA_DIR / "app_version.txt"


def parse_version(text: str) -> tuple[int, int, int]:
    parts = []
    for chunk in (text or "0").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits or 0))
        if len(parts) == 3:
            break
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def is_newer(candidate: str, current: str = APP_VERSION) -> bool:
    return parse_version(candidate) > parse_version(current)


def read_latest(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def check_for_update(source: Path | None = None) -> dict | None:
    """Preveri lokalni latest.json (ob installerju/updates)."""
    path = source or Path(__file__).resolve().parent.parent.parent / "updates" / "latest.json"
    try:
        from app.core.deploy_paths import install_root
        path = source or (install_root() / "updates" / "latest.json")
    except Exception:
        pass
    payload = read_latest(path)
    if not payload:
        return None
    remote = str(payload.get("version") or "")
    if remote and is_newer(remote):
        return payload
    return None


def backup_for_upgrade() -> Path:
    require("backup")
    controller = SettingsController()
    target = controller.backup_database()
    audit("upgrade-backup", str(target))
    logger.info("Varnostna kopija pred nadgradnjo: %s", target)
    return target


def rollback(backup: Path) -> None:
    require("backup")
    SettingsController().restore_database(backup)
    audit("upgrade-rollback", str(backup))
    logger.warning("Obnova baze po napaki nadgradnje: %s", backup)


def apply_schema_upgrade() -> None:
    """Po zamenjavi datotek: inicializiraj shemo, ob napaki rollback."""
    from app.database.database import db
    from app.core.setup_state import ensure_schema_version

    previous = VERSION_MARK.read_text(encoding="utf-8").strip() if VERSION_MARK.exists() else ""
    if previous == APP_VERSION:
        # Schema compatibility migrations must still run even when the app
        # version did not change. Branch restores can change the expected DB
        # shape while retaining the same public version number.
        db.initialize()
        ensure_schema_version()
        return
    backup = None
    if previous and DATABASE_PATH.exists():
        backup = backup_for_upgrade()
    try:
        db.initialize()
        ensure_schema_version()
        VERSION_MARK.write_text(APP_VERSION, encoding="utf-8")
        logger.info("Nadgradnja na %s uspešna (prej %s)", APP_VERSION, previous or "nova namestitev")
    except Exception:
        if backup is not None:
            rollback(backup)
        raise
