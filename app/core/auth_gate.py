"""Authentication gates for startup and logout.

``remember_user`` only pre-fills the username in UnlockDialog — it must never
bypass password authentication when a password is configured.
"""

from __future__ import annotations


def password_is_configured(extras: dict | None) -> bool:
    """True when settings contain a non-empty password hash."""
    if not extras:
        return False
    return bool(extras.get("password_hash"))


def startup_requires_authentication(extras: dict | None) -> bool:
    """Startup UnlockDialog is required iff a password is configured.

    Remember-user / saved UI session never skip this gate.
    """
    return password_is_configured(extras)


def logout_requires_reauth(extras: dict | None) -> bool:
    """After Odjava, return to UnlockDialog when a password is configured."""
    return password_is_configured(extras)
