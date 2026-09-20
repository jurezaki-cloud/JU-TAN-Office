"""Licensing use-cases, independent from the Qt user interface."""

from datetime import datetime, timezone

from .client import LicenseApiClient, LicenseApiError
from .models import LicenseState, LicenseStatus
from .storage import LicenseStore


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class LicenseService:
    def __init__(self, client: LicenseApiClient, store: LicenseStore, device_id: str, app_version: str):
        self.client = client
        self.store = store
        self.device_id = device_id
        self.app_version = app_version

    def activate(self, license_key: str) -> LicenseState:
        if not license_key.strip():
            raise ValueError("Vnesi licenčni ključ.")
        state = self._state_from_response(self.client.activate(license_key, self.device_id, self.app_version))
        self.store.save(state)
        return state

    def check(self) -> LicenseState:
        cached = self.store.load()
        if not cached.activation_token or cached.device_id != self.device_id:
            return LicenseState(device_id=self.device_id)
        try:
            state = self._state_from_response(
                self.client.validate(cached.activation_token, self.device_id, self.app_version)
            )
            self.store.save(state)
            return state
        except LicenseApiError as exc:
            grace_until = _parse(cached.grace_until)
            if exc.retryable and grace_until and _now() <= grace_until:
                return LicenseState(**{**cached.__dict__, "status": LicenseStatus.GRACE})
            raise

    def deactivate(self) -> None:
        cached = self.store.load()
        if cached.activation_token:
            self.client.deactivate(cached.activation_token, self.device_id)
        self.store.clear()

    def _state_from_response(self, payload: dict) -> LicenseState:
        state = LicenseState.from_dict({**payload, "device_id": self.device_id})
        if state.status not in {LicenseStatus.ACTIVE, LicenseStatus.GRACE}:
            raise LicenseApiError(payload.get("message", "Licenca ni veljavna."), retryable=False)
        return state
