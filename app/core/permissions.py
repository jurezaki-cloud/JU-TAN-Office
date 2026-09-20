"""RBAC, seje in trajni audit.

Roles provide permission presets. Per-user overrides live in SQLite
``user_permissions`` and are applied via :func:`set_identity` / session login.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from functools import wraps
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

ACTIONS = frozenset(
    {"read", "write", "delete", "export", "settings", "backup", "print", "users", "fresh"}
)

PERMISSIONS = {
    "Administrator": frozenset(
        {"read", "write", "delete", "export", "settings", "backup", "print", "users", "fresh"}
    ),
    "Manager": frozenset({"read", "write", "delete", "export", "settings", "print"}),
    "Sales": frozenset({"read", "write", "export", "print"}),
    "Warehouse": frozenset({"read", "write", "export", "print"}),
    "Accounting": frozenset({"read", "write", "export", "print", "backup"}),
    "Read Only": frozenset({"read"}),
}

ALLOWED = frozenset().union(*PERMISSIONS.values())
AUDIT_FILE = DATA_DIR / "audit.jsonl"

ALL_PAGES = frozenset(range(18))
ROLE_PAGES = {
    "Administrator": ALL_PAGES,
    "Manager": ALL_PAGES,
    "Sales": frozenset({0, 1, 2, 3, 4, 6, 9, 13, 14, 15, 17}),
    "Warehouse": frozenset({0, 4, 10, 11, 12, 13, 15}),
    "Accounting": frozenset({0, 1, 2, 6, 7, 8, 15, 17}),
    "Read Only": frozenset({0, 1, 2, 3, 4, 6, 9, 13, 14, 15, 17}),
}


def page_permission_key(index: int) -> str:
    return f"page:{int(index)}"


def role_default_permission_keys(role: str) -> list[str]:
    actions = PERMISSIONS.get(role, PERMISSIONS["Read Only"])
    pages = ROLE_PAGES.get(role, ROLE_PAGES["Read Only"])
    return actions_and_pages_to_permission_keys(actions, pages)


def actions_and_pages_to_permission_keys(actions, pages) -> list[str]:
    keys: list[str] = []
    for action in sorted(actions):
        if action in ACTIONS:
            keys.append(str(action))
    for index in sorted(int(p) for p in pages):
        keys.append(page_permission_key(index))
    return keys


def permission_keys_to_actions_pages(keys) -> tuple[frozenset[str], frozenset[int]]:
    actions: set[str] = set()
    pages: set[int] = set()
    for raw in keys or []:
        key = str(raw)
        if key.startswith("page:"):
            try:
                pages.add(int(key.split(":", 1)[1]))
            except ValueError:
                continue
        elif key in ACTIONS:
            actions.add(key)
    return frozenset(actions), frozenset(pages)


_state = {
    "role": "Administrator",
    "user": SESSION_USER,
    "user_id": None,
    "authenticated": True,
    "actions": None,  # None → derive from role
    "pages": None,  # None → derive from role
}


def current_role() -> str:
    return str(_state.get("role") or "Administrator")


def current_user() -> str:
    return str(_state.get("user") or SESSION_USER)


def current_user_id() -> int | None:
    value = _state.get("user_id")
    return int(value) if value is not None else None


def set_identity(
    *,
    user: str | None = None,
    role: str | None = None,
    authenticated: bool | None = None,
    user_id: int | None = None,
    actions: frozenset[str] | None = None,
    pages: frozenset[int] | None = None,
    clear_overrides: bool = False,
) -> None:
    if user is not None:
        _state["user"] = user
    if role is not None:
        if role not in PERMISSIONS:
            raise PermissionError("Neznana vloga.")
        _state["role"] = role
    if authenticated is not None:
        _state["authenticated"] = bool(authenticated)
    if user_id is not None or clear_overrides:
        _state["user_id"] = user_id
    if actions is not None or clear_overrides:
        _state["actions"] = frozenset(actions) if actions is not None else None
    if pages is not None or clear_overrides:
        _state["pages"] = frozenset(int(p) for p in pages) if pages is not None else None


def clear_identity() -> None:
    """Clear authenticated identity and permission overrides (logout / fresh)."""
    _state["authenticated"] = False
    _state["user_id"] = None
    _state["actions"] = None
    _state["pages"] = None


def _effective_actions() -> frozenset[str]:
    if _state.get("actions") is not None:
        return frozenset(_state["actions"])
    return PERMISSIONS.get(current_role(), PERMISSIONS["Read Only"])


def _effective_pages() -> frozenset[int]:
    if _state.get("pages") is not None:
        return frozenset(int(p) for p in _state["pages"])
    return ROLE_PAGES.get(current_role(), ROLE_PAGES["Read Only"])


def can(action: str) -> bool:
    if not _state.get("authenticated", True):
        return False
    return action in _effective_actions()


def require(action: str) -> None:
    if not can(action):
        logger.warning("Zavrnjena akcija: %s role=%s", action, current_role())
        raise PermissionError("Dejanje ni dovoljeno.")
    logger.debug("Dovoljena akcija: %s", action)


def allow(action: str, parent=None) -> bool:
    """RBAC za UI: False + prijazno sporočilo, če dejanje ni dovoljeno."""
    try:
        require(action)
        return True
    except PermissionError as exc:
        from app.core.errors import handle_error

        handle_error(exc, context="rbac", parent=parent)
        return False


def can_open_page(index: int) -> bool:
    if not can("read"):
        return False
    return int(index) in _effective_pages()


def gated(action: str, event: str | None = None):
    """Obvezen RBAC + audit okoli funkcije (telo CRUD ostane nespremenjeno)."""

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            require(action)
            result = fn(*args, **kwargs)
            detail = event or fn.__name__
            if len(args) > 1:
                detail = f"{detail}:{args[1]}"
            audit(action if event is None else event, str(detail)[:120])
            return result

        return wrapped

    return decorator


def _persist_audit(action: str, detail: str, user: str, user_id: int | None) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {"ts": stamp, "user": user, "action": action, "detail": detail}
    if user_id is not None:
        payload["user_id"] = user_id
    line = json.dumps(payload, ensure_ascii=False)
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
        # Prefer "username (id=N)" attribution when stable id is known.
        username = user
        if user_id is not None:
            username = f"{user}"
            detail_with_id = f"[uid={user_id}] {detail}" if detail else f"[uid={user_id}]"
            detail = detail_with_id
        conn.execute(
            "INSERT INTO audit_log(created_at, username, action, detail) VALUES (?,?,?,?)",
            (stamp, username, action, detail),
        )
        conn.commit()
        conn.close()
    except (sqlite3.Error, OSError):
        pass


def audit(action: str, detail: str = "") -> None:
    user = current_user()
    user_id = current_user_id()
    logger.info("AUDIT %s %s %s", user, action, detail)
    _persist_audit(action, detail, user, user_id)
