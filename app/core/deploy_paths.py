"""Poti namestitve — ProgramData ob installerju, sicer projekt/portable."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_FOLDER = "JU-TAN Office"


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_root() -> Path:
    if frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def install_config() -> dict:
    path = install_root() / "install.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def data_root() -> Path:
    """Korenska mapa za Data/Logs/Backup/Temp/Reports."""
    if os.environ.get("JU_TAN_DATA_DIR"):
        return Path(os.environ["JU_TAN_DATA_DIR"]).parent
    cfg = install_config()
    if cfg.get("data_root"):
        return Path(str(cfg["data_root"]))
    if cfg.get("mode") == "installed":
        programdata = os.environ.get("PROGRAMDATA") or r"C:\ProgramData"
        return Path(programdata) / APP_FOLDER
    if frozen():
        return install_root()
    return Path(__file__).resolve().parent.parent.parent


def data_folder_name() -> str:
    if install_config().get("mode") == "installed":
        return "Data"
    return "data"


def resolve_dir(env_name: str, *parts: str) -> Path:
    override = os.environ.get(env_name)
    if override:
        path = Path(override)
    else:
        path = data_root().joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path
