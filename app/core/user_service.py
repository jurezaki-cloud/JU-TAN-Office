"""Multi-user business logic: bootstrap, migration, CRUD, last-admin protection."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from typing import Any, Literal

from app.core.passwords import hash_password, verify_password
from app.core.permissions import (
    ACTIONS,
    AUDIT_FILE,
    PERMISSIONS,
    ROLE_PAGES,
    ROLES,
    actions_and_pages_to_permission_keys,
    permission_keys_to_actions_pages,
    role_default_permission_keys,
)
from app.database.user_repository import normalize_username, user_repository

RemovalMode = Literal["physical", "archive"]

# Slovenian UI labels for roles (internal keys stay English for compatibility).
ROLE_LABELS = {
    "Administrator": "Administrator",
    "Manager": "Vodja",
    "Sales": "Prodaja",
    "Warehouse": "Skladišče",
    "Accounting": "Računovodstvo",
    "Read Only": "Samo za branje",
}

# UI-facing role choices (presets). Custom permissions → display "Po meri".
UI_ROLE_PRESETS = (
    "Administrator",
    "Sales",
    "Read Only",
    "Manager",
    "Warehouse",
    "Accounting",
)

AUTH_ERROR_MESSAGE = "Uporabniško ime ali geslo ni pravilno."

# Page area labels for user-management checkboxes
PAGE_PERMISSION_LABELS: list[tuple[str, int]] = [
    ("Nadzorna plošča", 0),
    ("Računi", 1),
    ("Ponudbe", 3),
    ("Naročila", 9),
    ("Stranke", 2),
    ("Artikli", 4),
    ("Skladišče", 10),
    ("Dobavitelji", 11),
    ("Nabava", 12),
    ("Plačila", 6),
    ("Analitika", 7),
    ("Poročila", 15),
    ("Dokumenti", 13),
    ("CRM", 14),
    ("Potni nalogi", 17),
    ("Avtomatizacija", 16),
    ("Podjetje", 5),
    ("Nastavitve", 8),
]

ACTION_PERMISSION_LABELS: list[tuple[str, str]] = [
    ("Branje", "read"),
    ("Ustvarjanje / urejanje", "write"),
    ("Brisanje / preklic", "delete"),
    ("Izvoz", "export"),
    ("Tiskanje", "print"),
    ("Nastavitve (shranjevanje)", "settings"),
    ("Varnostne kopije", "backup"),
    ("Uporabniki in pravice", "users"),
    ("Ponastavitev FRESH", "fresh"),
]


class LastAdminError(PermissionError):
    """Raised when an operation would remove the last active administrator."""


class SelfRemovalError(PermissionError):
    """Raised when removing the currently authenticated session user."""


@dataclass(frozen=True)
class RemovalAssessment:
    """Result of auditing whether a user may be erased or only archived."""

    user_id: int
    username: str
    mode: RemovalMode
    has_history: bool


def users_exist() -> bool:
    user_repository.ensure_schema()
    return user_repository.count_users() > 0


def public_user(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """Safe account metadata — never expose password_hash."""
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "is_active": row["is_active"],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "last_login_at": row.get("last_login_at"),
        "permissions": user_repository.get_permissions(row["id"]),
    }


def list_public_users() -> list[dict[str, Any]]:
    from app.core.permissions import require

    require("users")
    return [public_user(u) for u in user_repository.list_users()]  # type: ignore[misc]


def effective_permission_keys(user: dict[str, Any]) -> frozenset[str]:
    """Deterministic effective permissions for a user row."""
    stored = user_repository.get_permissions(user["id"])
    if stored:
        return frozenset(stored)
    return frozenset(role_default_permission_keys(user["role"]))


def authenticate_user(username: str, password: str) -> tuple[dict[str, Any] | None, str | None]:
    """Validate against SQLite users. Generic error on any failure."""
    user_repository.ensure_schema()
    provided = (username or "").strip()
    # Always attempt a verify path to reduce username-existence timing leaks.
    user = user_repository.get_by_username(provided) if provided else None
    stored_hash = (user or {}).get("password_hash") or ""
    pwd_ok = verify_password(password or "", stored_hash) if stored_hash else False
    if user is None or not user.get("is_active") or not pwd_ok:
        # Dummy verify when no hash to keep work similar
        if not stored_hash:
            verify_password(password or "x", "scrypt:AAAAAAAAAAAAAAAAAAAAAA==:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        return None, AUTH_ERROR_MESSAGE
    return user, None


def create_first_administrator(username: str, password: str) -> dict[str, Any]:
    """Create the first user as Administrator with full permissions.

    Transactionally safe: refuses if any user already exists.
    """
    user_repository.ensure_schema()
    if user_repository.count_users() > 0:
        raise PermissionError("Prvi uporabnik že obstaja.")
    display = (username or "").strip()
    if not display:
        raise ValueError("Uporabniško ime je obvezno.")
    hashed = hash_password(password)
    perms = list(role_default_permission_keys("Administrator"))
    user_id = user_repository.create_user(
        username=display,
        password_hash=hashed,
        role="Administrator",
        is_active=True,
        permissions=perms,
    )
    row = user_repository.get_by_id(user_id)
    assert row is not None
    return row


def create_user(
    *,
    username: str,
    password: str,
    role: str,
    is_active: bool = True,
    permissions: list[str] | None = None,
) -> dict[str, Any]:
    from app.core.permissions import audit, require

    require("users")
    if role not in PERMISSIONS:
        raise ValueError("Neznana vloga.")
    display = (username or "").strip()
    if not display:
        raise ValueError("Uporabniško ime je obvezno.")
    hashed = hash_password(password)
    keys = permissions if permissions is not None else list(role_default_permission_keys(role))
    # Non-first users never auto-admin unless explicitly assigned.
    user_id = user_repository.create_user(
        username=display,
        password_hash=hashed,
        role=role,
        is_active=is_active,
        permissions=keys,
    )
    audit("users", f"create:{display}")
    row = user_repository.get_by_id(user_id)
    assert row is not None
    return row


def update_user(
    user_id: int,
    *,
    username: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    permissions: list[str] | None = None,
) -> dict[str, Any]:
    from app.core.permissions import audit, require

    require("users")
    current = user_repository.get_by_id(user_id)
    if current is None:
        raise ValueError("Uporabnik ne obstaja.")

    new_role = role if role is not None else current["role"]
    if new_role not in PERMISSIONS:
        raise ValueError("Neznana vloga.")
    new_active = current["is_active"] if is_active is None else bool(is_active)
    new_perms = (
        permissions
        if permissions is not None
        else user_repository.get_permissions(user_id) or list(role_default_permission_keys(new_role))
    )

    would_lose_admin = _would_lose_admin_capability(
        current,
        new_role=new_role,
        new_active=new_active,
        new_perms=new_perms,
    )
    if would_lose_admin and user_repository.count_active_admins() <= 1:
        raise LastAdminError(
            "Ni mogoče odstraniti zadnjega aktivnega administratorja. "
            "Najprej dodelite skrbniške pravice drugemu uporabniku."
        )

    user_repository.update_user(
        user_id,
        username=username,
        role=new_role,
        is_active=new_active,
        permissions=new_perms,
    )
    audit("users", f"update:{user_id}")
    row = user_repository.get_by_id(user_id)
    assert row is not None
    return row


def reset_user_password(user_id: int, new_password: str) -> None:
    from app.core.permissions import audit, require

    require("users")
    current = user_repository.get_by_id(user_id)
    if current is None:
        raise ValueError("Uporabnik ne obstaja.")
    hashed = hash_password(new_password)
    user_repository.set_password_hash(user_id, hashed)
    audit("users", f"reset-password:{user_id}")


def change_own_password(user_id: int, old_password: str, new_password: str) -> None:
    """Change password for the authenticated user — no role escalation."""
    from app.core.permissions import audit

    current = user_repository.get_by_id(user_id)
    if current is None:
        raise ValueError("Uporabnik ne obstaja.")
    if not verify_password(old_password or "", current["password_hash"]):
        raise PermissionError("Trenutno geslo ni pravilno.")
    hashed = hash_password(new_password)
    user_repository.set_password_hash(user_id, hashed)
    audit("users", f"change-own-password:{user_id}")


def user_has_historical_references(user_id: int, username: str) -> bool:
    """True when the user is referenced by audit / operational history.

    Business documents (invoices, offers, payments, …) do not store user FKs;
    accountability lives in audit trails and named operational logs.
    """
    if user_repository.count_audit_actor_references(user_id, username) > 0:
        return True
    if _audit_file_references(user_id, username):
        return True
    if _warehouse_movement_references(username):
        return True
    if _automation_run_references(username):
        return True
    return False


def assess_user_removal(user_id: int) -> RemovalAssessment:
    """Decide physical delete vs archive without mutating state."""
    from app.core.permissions import require

    require("users")
    current = user_repository.get_by_id(user_id)
    if current is None:
        raise ValueError("Uporabnik ne obstaja.")
    has_history = user_has_historical_references(current["id"], current["username"])
    return RemovalAssessment(
        user_id=int(current["id"]),
        username=current["username"],
        mode="archive" if has_history else "physical",
        has_history=has_history,
    )


def remove_user(user_id: int) -> RemovalAssessment:
    """Remove access for a user: physical delete when safe, else archive.

    Protections (service layer — not UI-only):
    - requires ``users`` permission
    - refuses removing the currently logged-in session user
    - refuses removing the last active administrator / user-manager
    """
    from app.core.permissions import audit, require

    require("users")
    current = user_repository.get_by_id(user_id)
    if current is None:
        raise ValueError("Uporabnik ne obstaja.")

    if _has_admin_capability(current) and user_repository.count_active_admins() <= 1:
        raise LastAdminError(
            "Ni mogoče odstraniti zadnjega aktivnega administratorja. "
            "Najprej dodelite skrbniške pravice drugemu uporabniku."
        )

    if _is_current_session_user(current):
        raise SelfRemovalError(
            "Ni mogoče odstraniti trenutno prijavljenega uporabnika. "
            "Najprej se odjavite ali odstranite drugega skrbnika."
        )

    assessment = assess_user_removal(user_id)
    if assessment.mode == "physical":
        user_repository.delete_user(user_id)
        audit("users", f"remove-physical:{assessment.username}")
        return assessment

    # Archive: keep stable id + username; revoke access without erasing history.
    scrambled = hash_password(secrets.token_urlsafe(32))
    if current["role"] == "Administrator" or "users" in set(
        user_repository.get_permissions(user_id)
    ):
        new_role = "Read Only"
        new_perms = list(role_default_permission_keys("Read Only"))
    else:
        new_role = current["role"]
        new_perms = [
            key
            for key in (
                user_repository.get_permissions(user_id)
                or list(role_default_permission_keys(new_role))
            )
            if key not in {"users", "fresh", "settings", "backup"}
        ]

    user_repository.update_user(
        user_id,
        role=new_role,
        is_active=False,
        password_hash=scrambled,
        permissions=new_perms,
    )
    audit("users", f"remove-archive:{assessment.username}")
    return assessment


def _is_current_session_user(user: dict[str, Any]) -> bool:
    from app.core.session import session

    if session.user_id is not None and int(session.user_id) == int(user["id"]):
        return True
    session_name = (session.user or "").strip()
    if session_name and normalize_username(session_name) == user.get("username_normalized"):
        # Only treat as self when the session is actually authenticated.
        return bool(getattr(session, "authenticated", False))
    return False


def _audit_file_references(user_id: int, username: str) -> bool:
    path = AUDIT_FILE
    if not path.exists():
        return False
    key = normalize_username(username)
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("user_id") == user_id:
                    return True
                if normalize_username(str(payload.get("user") or "")) == key:
                    return True
    except OSError:
        return False
    return False


def _warehouse_movement_references(username: str) -> bool:
    from app.core.constants import DATA_DIR

    path = DATA_DIR / "warehouse.json"
    if not path.exists():
        return False
    key = normalize_username(username)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    for movement in data.get("movements") or []:
        if normalize_username(str(movement.get("user") or "")) == key:
            return True
    return False


def _automation_run_references(username: str) -> bool:
    try:
        from app.database.database import db

        key = (username or "").strip()
        if not key:
            return False
        conn = db.connect()
        try:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='automation_runs'"
            ).fetchone()
            if not exists:
                return False
            row = conn.execute(
                """
                SELECT COUNT(*) FROM automation_runs
                WHERE lower(IFNULL(user_name, '')) = lower(?)
                """,
                (key,),
            ).fetchone()
            return int(row[0] if row else 0) > 0
        finally:
            conn.close()
    except Exception:
        return False


def _would_lose_admin_capability(
    current: dict[str, Any],
    *,
    new_role: str,
    new_active: bool,
    new_perms: list[str],
) -> bool:
    was_admin = _has_admin_capability(current)
    if not was_admin:
        return False
    will_have = new_active and (
        new_role == "Administrator" or "users" in set(new_perms)
    )
    return was_admin and not will_have


def _has_admin_capability(user: dict[str, Any]) -> bool:
    if not user.get("is_active"):
        return False
    if user.get("role") == "Administrator":
        return True
    return "users" in set(user_repository.get_permissions(user["id"]))


def migrate_legacy_settings_auth(extras: dict) -> dict:
    """Idempotent: migrate settings.json credentials into SQLite users.

    Scenario A: valid hash → create first user (preserve hash, no re-hash).
    Scenario B: setup_complete but no hash → leave users empty (onboarding).
    Scenario C: username 'Administrator' preserved as display; owner may rename later.

    After successful migration, clears active settings auth fields so SQLite
    is the sole authentication source of truth.
    """
    user_repository.ensure_schema()
    if user_repository.count_users() > 0:
        # Already migrated — ensure legacy auth fields are retired.
        return _retire_legacy_auth_fields(extras)

    hash_value = (extras.get("password_hash") or "").strip()
    if not hash_value:
        return extras

    username = (extras.get("administrator") or "").strip() or "Administrator"
    role = (extras.get("role") or "Administrator").strip()
    if role not in PERMISSIONS:
        role = "Administrator"
    is_active = extras.get("account_enabled", True) is not False

    # Insert preserving existing hash (already Argon2id/scrypt).
    perms = list(role_default_permission_keys(role))
    try:
        user_repository.create_user(
            username=username,
            password_hash=hash_value,
            role=role,
            is_active=is_active,
            permissions=perms,
        )
    except ValueError:
        # Race / already created
        if user_repository.count_users() == 0:
            raise

    return _retire_legacy_auth_fields(extras)


def _retire_legacy_auth_fields(extras: dict) -> dict:
    """Clear competing settings auth so SQLite is the only login path."""
    updated = dict(extras)
    updated["password_hash"] = ""
    # Keep administrator as remembered-username hint only when remember_user is on.
    # Do not keep it as an auth identity.
    updated["legacy_auth_migrated"] = True
    return updated


def apply_session_for_user(user: dict[str, Any]) -> None:
    """Load identity + effective permissions into session/RBAC state."""
    from app.core.session import session

    keys = effective_permission_keys(user)
    actions, pages = permission_keys_to_actions_pages(keys)
    session.login(
        user["username"],
        user["role"],
        user_id=user["id"],
        actions=actions,
        pages=pages,
    )
    user_repository.touch_last_login(user["id"])


def permissions_differ_from_role(role: str, permission_keys: list[str] | frozenset[str]) -> bool:
    defaults = frozenset(role_default_permission_keys(role))
    return frozenset(permission_keys) != defaults


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def display_role_for_user(user: dict[str, Any]) -> str:
    perms = user.get("permissions")
    if perms is None:
        perms = user_repository.get_permissions(user["id"])
    if perms and permissions_differ_from_role(user["role"], perms):
        return "Po meri"
    return role_label(user["role"])


# Re-exports used by UI
__all__ = [
    "ACTIONS",
    "ACTION_PERMISSION_LABELS",
    "AUTH_ERROR_MESSAGE",
    "LastAdminError",
    "PAGE_PERMISSION_LABELS",
    "RemovalAssessment",
    "ROLE_LABELS",
    "ROLES",
    "SelfRemovalError",
    "UI_ROLE_PRESETS",
    "actions_and_pages_to_permission_keys",
    "apply_session_for_user",
    "assess_user_removal",
    "authenticate_user",
    "change_own_password",
    "create_first_administrator",
    "create_user",
    "display_role_for_user",
    "effective_permission_keys",
    "list_public_users",
    "migrate_legacy_settings_auth",
    "normalize_username",
    "permissions_differ_from_role",
    "public_user",
    "remove_user",
    "reset_user_password",
    "role_default_permission_keys",
    "role_label",
    "update_user",
    "user_has_historical_references",
    "users_exist",
]
