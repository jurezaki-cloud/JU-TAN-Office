"""RBAC, seje in trajni audit."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.constants import DATA_DIR
from app.core.logger import SESSION_USER, logger

ROLES = (
    "Administrator",
    "Manager",
    "Sales",
    "Warehouse",
    "Accounting",
    "Read Only",
)

PERMISSIONS = {
    "Administrator": frozenset({"read", "write", "delete", "export", "settings", "backup", "print", "users"}),
    "Manager": frozenset({"read", "write", "delete", "export", "settings", "print"}),
    "Sales": frozenset({"read", "write", "export", "print"}),
    "Warehouse": frozenset({"read", "write", "export"}),
    "Accounting": frozenset({"read", "write", "export", "print", "backup"}),
    "Read Only": frozenset({"read"}),
}

ALLOWED = frozenset().union(*PERMISSIONS.values())
AUDIT_FILE = DATA_DIR / "audit.jsonl"

_state = {
    "role": "Administrator",
    "user": SESSION_USER,
    "authenticated": True,
}


def current_role() -> str:
    return str(_state.get("role") or "Administrator")


def current_user() -> str:
    return str(_state.get("user") or SESSION_USER)


def set_identity(*, user: str | None = None, role: str | None = None, authenticated: bool | None = None) -> None:
    if user is not None:
        _state["user"] = user
    if role is not None:
        if role not in PERMISSIONS:
            raise PermissionError("Neznana vloga.")
        _state["role"] = role
    if authenticated is not None:
        _state["authenticated"] = bool(authenticated)


def can(action: str) -> bool:
    if not _state.get("authenticated", True):
        return False
    granted = PERMISSIONS.get(current_role(), PERMISSIONS["Read Only"])
    return action in granted


def require(action: str) -> None:
    if not can(action):
        logger.warning("Zavrnjena akcija: %s role=%s", action, current_role())
        raise PermissionError("Dejanje ni dovoljeno.")
    logger.debug("Dovoljena akcija: %s", action)


def _persist_audit(action: str, detail: str, user: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = json.dumps({"ts": stamp, "user": user, "action": action, "detail": detail}, ensure_ascii=False)
    try:
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass
    try:
        from app.database.database import db

        conn = db.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                username TEXT,
                action TEXT NOT NULL,
                detail TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO audit_log(created_at, username, action, detail) VALUES (?,?,?,?)",
            (stamp, user, action, detail),
        )
        conn.commit()
        conn.close()
    except (sqlite3.Error, OSError):
        pass


def audit(action: str, detail: str = "") -> None:
    user = current_user()
    logger.info("AUDIT %s %s %s", user, action, detail)
    _persist_audit(action, detail, user)
