"""Obnovitev po sesutju: zastavica, seja, osnutki, rollback WAL."""

from __future__ import annotations

import atexit
import json
from pathlib import Path

from app.core.constants import DATA_DIR
from app.core.logger import logger
from app.core.permissions import audit

FLAG = DATA_DIR / "crash.flag"
SESSION_FILE = DATA_DIR / "session.json"
DRAFT_DIR = DATA_DIR / "drafts"


def mark_running() -> bool:
    """True, če je prejšnji zagon ostal odprt (sesutje)."""
    crashed = FLAG.exists()
    FLAG.write_text("running", encoding="utf-8")
    atexit.register(clear_running)
    if crashed:
        logger.warning("Zaznano morebitno sesutje — WAL/osnutki.")
        audit("crash-recovery", str(FLAG))
        try:
            from app.core.db_guard import recover_after_crash

            recover_after_crash()
        except Exception as exc:
            logger.error("Obnova po sesutju: %s", exc)
    return crashed


def clear_running() -> None:
    try:
        if FLAG.exists():
            FLAG.unlink()
    except OSError:
        pass


def save_ui_session(payload: dict) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_ui_session() -> dict:
    if not SESSION_FILE.exists():
        return {}
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_draft(name: str, payload: dict) -> Path:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    path = DRAFT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def load_draft(name: str) -> dict:
    path = DRAFT_DIR / f"{name}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}
