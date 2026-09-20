"""Authentication gates for startup, logout, and credential checks.

``remember_user`` only pre-fills the username in UnlockDialog — it must never
bypass password authentication when credentials are configured.

Preferred source of truth: SQLite ``users`` table. Legacy ``settings.json``
password_hash remains supported until migrated via :func:`ensure_auth_migrated`.
"""

from __future__ import annotations

from typing import Any

from app.core.passwords import verify_password

# Generic Slovenian failure — never reveal whether username or password failed.
AUTH_ERROR_MESSAGE = "Uporabniško ime ali geslo ni pravilno."


def _users_available() -> bool:
    try:
        from app.core.user_service import users_exist

        return users_exist()
    except Exception:
        return False


def password_is_configured(extras: dict | None) -> bool:
    """True when SQLite users exist or settings contain a non-empty password hash."""
    if _users_available():
        return True
    if not extras:
        return False
    return bool(extras.get("password_hash"))


def account_is_enabled(extras: dict | None) -> bool:
    """Disabled legacy accounts cannot authenticate. Default is enabled."""
    if not extras:
        return True
    return extras.get("account_enabled", True) is not False


def needs_credential_onboarding(extras: dict | None) -> bool:
    """Existing install finished setup but has no usable credentials.

    Idempotent: once SQLite users or ``password_hash`` exist, returns False.
    """
    if not extras:
        return False
    if not extras.get("setup_complete"):
        return False
    if _users_available():
        return False
    return not bool(extras.get("password_hash"))


def ensure_auth_migrated(extras: dict | None) -> dict:
    """Idempotent: migrate legacy settings credentials into SQLite users."""
    from app.core.user_service import migrate_legacy_settings_auth
    from app.modules.settings.settings_controller import SettingsController

    data = dict(extras or {})
    migrated = migrate_legacy_settings_auth(data)
    if migrated != data:
        SettingsController().save_extras_unrestricted(migrated)
    return migrated


def startup_requires_authentication(extras: dict | None) -> bool:
    """Startup login is required whenever usable credentials exist.

    Remember-user / saved UI session never skip this gate.
    """
    return password_is_configured(extras)


def logout_requires_reauth(extras: dict | None) -> bool:
    """After Odjava, return to UnlockDialog when credentials are configured."""
    return password_is_configured(extras)


def usernames_match(provided: str | None, expected: str | None) -> bool:
    """Case-insensitive username compare (trimmed)."""
    return (provided or "").strip().casefold() == (expected or "").strip().casefold()


def authenticate_credentials(
    username: str,
    password: str,
    extras: dict | None,
) -> tuple[bool, str | None]:
    """Validate username + password.

    Prefers SQLite users when present; otherwise legacy settings hash.
    Returns ``(True, None)`` on success, or ``(False, AUTH_ERROR_MESSAGE)``.
    """
    if _users_available():
        from app.core.user_service import authenticate_user

        user, err = authenticate_user(username, password)
        if user is None:
            return False, err or AUTH_ERROR_MESSAGE
        return True, None

    if not extras or not extras.get("password_hash"):
        return False, AUTH_ERROR_MESSAGE
    if not account_is_enabled(extras):
        return False, AUTH_ERROR_MESSAGE

    expected_user = (extras.get("administrator") or "Administrator").strip()
    user_ok = usernames_match(username, expected_user)
    # Always run password verification to avoid trivial username-only short-circuit
    # timing differences when a hash is present.
    pwd_ok = verify_password(password or "", extras.get("password_hash") or "")
    if not (user_ok and pwd_ok):
        return False, AUTH_ERROR_MESSAGE
    return True, None


def resolve_authenticated_user(
    username: str,
    password: str,
    extras: dict | None,
) -> dict[str, Any] | None:
    """Return the SQLite user row on success, or None for legacy/settings auth."""
    if not _users_available():
        return None
    from app.core.user_service import authenticate_user

    user, _err = authenticate_user(username, password)
    return user


def authenticated_role(extras: dict | None, *, username: str | None = None) -> str:
    """Role for the authenticated account.

    When SQLite users exist, prefer the user's stored role; otherwise settings.
    """
    if _users_available() and username:
        from app.database.user_repository import user_repository

        row = user_repository.get_by_username(username)
        if row is not None:
            return row.get("role") or "Administrator"
    if not extras:
        return "Administrator"
    return (extras.get("role") or "Administrator").strip() or "Administrator"
