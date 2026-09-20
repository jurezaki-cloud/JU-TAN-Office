import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.licensing.client import LicenseApiError
from app.licensing.models import LicenseState, LicenseStatus
from app.licensing.service import LicenseService
from app.licensing.storage import LicenseStore


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def activate(self, *_args):
        if self.error:
            raise self.error
        return self.response

    validate = activate

    def deactivate(self, *_args):
        return {"ok": True}


def payload(**extra):
    return {
        "status": "active",
        "license_id": "lic_1",
        "company_name": "Test d.o.o.",
        "activation_token": "signed-token",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def test_store_round_trip():
    with tempfile.TemporaryDirectory() as directory:
        store = LicenseStore(Path(directory) / "license.json")
        expected = LicenseState(status=LicenseStatus.ACTIVE, activation_token="token")
        store.save(expected)
        assert store.load() == expected


def test_activate_persists_server_state(tmp_path):
    store = LicenseStore(tmp_path / "license.json")
    service = LicenseService(FakeClient(payload()), store, "device-1", "0.2.0")
    state = service.activate("jt-demo-key")
    assert state.status is LicenseStatus.ACTIVE
    assert state.device_id == "device-1"
    assert store.load().activation_token == "signed-token"


def test_retryable_outage_uses_unexpired_grace(tmp_path):
    store = LicenseStore(tmp_path / "license.json")
    store.save(LicenseState(
        status=LicenseStatus.ACTIVE,
        activation_token="token",
        device_id="device-1",
        grace_until=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    ))
    service = LicenseService(
        FakeClient(error=LicenseApiError("offline", retryable=True)),
        store,
        "device-1",
        "0.2.0",
    )
    assert service.check().status is LicenseStatus.GRACE


def test_non_retryable_rejection_never_uses_grace(tmp_path):
    store = LicenseStore(tmp_path / "license.json")
    store.save(LicenseState(
        status=LicenseStatus.ACTIVE,
        activation_token="token",
        device_id="device-1",
        grace_until=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    ))
    service = LicenseService(
        FakeClient(error=LicenseApiError("blocked", retryable=False)),
        store,
        "device-1",
        "0.2.0",
    )
    with pytest.raises(LicenseApiError):
        service.check()
