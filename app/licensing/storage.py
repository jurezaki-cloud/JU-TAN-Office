"""Atomic local storage for server-issued activation state."""

import json
import os
import tempfile
from pathlib import Path

from .models import LicenseState


class LicenseStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> LicenseState:
        try:
            with self.path.open(encoding="utf-8") as handle:
                value = json.load(handle)
            return LicenseState.from_dict(value)
        except (OSError, ValueError, TypeError):
            return LicenseState()

    def save(self, state: LicenseState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="license-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state.to_dict(), handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
