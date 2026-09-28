"""JU-TAN Office owned filesystem locations (installer / uninstall audit).

Business data cleanup must only touch paths listed here.
Never delete user exports outside these roots.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.deploy_paths import APP_FOLDER, data_root, install_config, install_root
from app.services.licensing_service import STATE_DIR as LICENSE_STATE_DIR


@dataclass(frozen=True)
class DataLocation:
    """One owned path category."""

    key: str
    path: Path
    kind: str  # business | runtime | license | install | backup | export
    description: str
    removable_on_standard_uninstall: bool
    removable_on_complete_uninstall: bool
    removable_on_fresh_install: bool


def programdata_root() -> Path:
    programdata = os.environ.get("PROGRAMDATA") or r"C:\ProgramData"
    return Path(programdata) / APP_FOLDER


def appdata_roaming_root() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "JU-TAN"


def localappdata_license_root() -> Path:
    return Path(LICENSE_STATE_DIR)


def installed_app_dir() -> Path:
    cfg = install_config()
    if cfg.get("mode") == "installed" or getattr(
        __import__("sys"), "frozen", False
    ):
        return install_root()
    return Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "JU-TAN Office"


def owned_locations(*, runtime_root: Path | None = None) -> list[DataLocation]:
    """Canonical inventory of JU-TAN-owned locations.

    ``runtime_root`` overrides the active data root (tests / portable).
    """
    root = Path(runtime_root) if runtime_root is not None else data_root()
    pd = programdata_root()
    return [
        DataLocation(
            key="programdata_root",
            path=pd,
            kind="business",
            description="Machine-wide application data (installed mode)",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=False,
        ),
        DataLocation(
            key="data",
            path=root / ("Data" if (root / "Data").exists() or install_config().get("mode") == "installed" else "data"),
            kind="business",
            description="Database, settings, documents, warehouse JSON",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=True,
        ),
        DataLocation(
            key="logs",
            path=root / "Logs" if (root / "Logs").parent == root else root / "logs",
            kind="runtime",
            description="Application logs",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=True,
        ),
        DataLocation(
            key="backup",
            path=root / "Backup" if (root / "Backup").exists() or install_config().get("mode") == "installed" else root / "Backup",
            kind="backup",
            description="Local backups (including pre-upgrade / FreshReset)",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=False,  # requires extra checkbox
            removable_on_fresh_install=False,
        ),
        DataLocation(
            key="temp",
            path=root / "Temp",
            kind="runtime",
            description="Temporary files",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=True,
        ),
        DataLocation(
            key="reports",
            path=root / "Reports",
            kind="export",
            description="In-app report / export staging under JU-TAN root",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=True,
        ),
        DataLocation(
            key="license_activation",
            path=localappdata_license_root(),
            kind="license",
            description="Online activation / device bind (LocalAppData)",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=False,
            removable_on_fresh_install=False,
        ),
        DataLocation(
            key="install_dir",
            path=installed_app_dir(),
            kind="install",
            description="Program Files / portable install tree",
            removable_on_standard_uninstall=True,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=False,
        ),
        DataLocation(
            key="appdata_roaming_legacy",
            path=appdata_roaming_root(),
            kind="runtime",
            description="Legacy/optional Roaming AppData (not primary store)",
            removable_on_standard_uninstall=False,
            removable_on_complete_uninstall=True,
            removable_on_fresh_install=False,
        ),
    ]


def business_data_markers(data_dir: Path) -> list[Path]:
    """Files/dirs that indicate previous business installation data."""
    return [
        data_dir / "ju_tan.db",
        data_dir / "ju_tan.db-wal",
        data_dir / "ju_tan.db-shm",
        data_dir / "settings.json",
        data_dir / "warehouse.json",
        data_dir / "documents",
        data_dir / "session.json",
        data_dir / "audit.jsonl",
    ]


def previous_business_data_exists(data_dir: Path) -> bool:
    for path in business_data_markers(data_dir):
        if path.is_file() or (path.is_dir() and any(path.iterdir())):
            return True
    return False


__all__ = [
    "DataLocation",
    "appdata_roaming_root",
    "business_data_markers",
    "installed_app_dir",
    "localappdata_license_root",
    "owned_locations",
    "previous_business_data_exists",
    "programdata_root",
]
