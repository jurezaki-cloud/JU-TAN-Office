"""Seja: timeout, zaklep, prijava, odjava."""

from __future__ import annotations

import time

from app.core.logger import SESSION_USER
from app.core.permissions import audit, clear_identity, current_role, set_identity

DEFAULT_TIMEOUT_SEC = 30 * 60


class Session:
    def __init__(self) -> None:
        self.user = SESSION_USER
        self.user_id: int | None = None
        self.role = "Administrator"
        self.remember_user = True
        self.timeout_sec = DEFAULT_TIMEOUT_SEC
        self.last_activity = time.monotonic()
        self.locked = False
        self.authenticated = True
        self.actions: frozenset[str] | None = None
        self.pages: frozenset[int] | None = None

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def idle_seconds(self) -> float:
        return max(0.0, time.monotonic() - self.last_activity)

    def idle_too_long(self) -> bool:
        if self.timeout_sec <= 0:
            return False
        return self.idle_seconds() >= self.timeout_sec

    def login(
        self,
        user: str,
        role: str = "Administrator",
        *,
        user_id: int | None = None,
        actions: frozenset[str] | None = None,
        pages: frozenset[int] | None = None,
    ) -> None:
        self.user = user
        self.user_id = user_id
        self.role = role or "Administrator"
        self.actions = actions
        self.pages = pages
        self.locked = False
        self.authenticated = True
        self.touch()
        set_identity(
            user=user,
            role=self.role,
            authenticated=True,
            user_id=user_id,
            actions=actions,
            pages=pages,
            clear_overrides=True,
        )
        audit("login", user)

    def logout(self) -> None:
        audit("logout", self.user)
        self.authenticated = False
        self.locked = True
        self.user_id = None
        self.actions = None
        self.pages = None
        clear_identity()

    def lock(self) -> None:
        if not self.locked:
            audit("lock", self.user)
        self.locked = True
        set_identity(authenticated=False)

    def unlock(self, user: str | None = None) -> None:
        self.locked = False
        self.authenticated = True
        self.touch()
        role = self.role or current_role()
        set_identity(
            user=user or self.user,
            role=role,
            authenticated=True,
            user_id=self.user_id,
            actions=self.actions,
            pages=self.pages,
        )
        audit("unlock", self.user)

    def clear(self) -> None:
        """Full session wipe (Fresh reset)."""
        self.user = SESSION_USER
        self.user_id = None
        self.role = "Administrator"
        self.actions = None
        self.pages = None
        self.authenticated = False
        self.locked = True
        clear_identity()


session = Session()
