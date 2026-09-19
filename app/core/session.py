"""Seja: timeout, zaklep, prijava, odjava."""

from __future__ import annotations

import time

from app.core.logger import SESSION_USER
from app.core.permissions import audit, current_role, set_identity

DEFAULT_TIMEOUT_SEC = 30 * 60


class Session:
    def __init__(self) -> None:
        self.user = SESSION_USER
        self.role = "Administrator"
        self.remember_user = True
        self.timeout_sec = DEFAULT_TIMEOUT_SEC
        self.last_activity = time.monotonic()
        self.locked = False
        self.authenticated = True

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def idle_seconds(self) -> float:
        return max(0.0, time.monotonic() - self.last_activity)

    def idle_too_long(self) -> bool:
        if self.timeout_sec <= 0:
            return False
        return self.idle_seconds() >= self.timeout_sec

    def login(self, user: str, role: str = "Administrator") -> None:
        self.user = user
        self.role = role or "Administrator"
        self.locked = False
        self.authenticated = True
        self.touch()
        set_identity(user=user, role=self.role, authenticated=True)
        audit("login", user)

    def logout(self) -> None:
        audit("logout", self.user)
        self.authenticated = False
        self.locked = True
        set_identity(authenticated=False)

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
        set_identity(user=user or self.user, role=role, authenticated=True)
        audit("unlock", self.user)


session = Session()
