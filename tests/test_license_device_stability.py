"""Stable device identity and existing DPAPI activation migration."""
import json
import pytest
from app.services import licensing_service as lic


@pytest.fixture
def windows_state(tmp_path, monkeypatch):
    monkeypatch.setattr(lic, "STATE_DIR", tmp_path)
    monkeypatch.setattr(lic, "STATE_FILE", tmp_path / "license.json")
    monkeypatch.setattr(lic.platform, "system", lambda: "Windows")
    monkeypatch.setattr(lic, "_windows_machine_guid", lambda: "machine-A")
    monkeypatch.setattr(lic, "_dpapi_protect", lambda value: "dpapi:" + value)
    monkeypatch.setattr(lic, "_dpapi_unprotect", lambda value: value.removeprefix("dpapi:"))


def test_new_identity_ignores_network_and_hostname(windows_state, monkeypatch):
    original = lic.device_id()
    monkeypatch.setattr(lic.platform, "node", lambda: "renamed-PC")
    monkeypatch.setattr(lic.uuid, "getnode", lambda: 999)
    assert lic.device_id() == original


def test_legacy_token_keeps_server_identity(windows_state, monkeypatch):
    lic.STATE_FILE.write_text(json.dumps({"activation_token": "dpapi:token", "device_id": "a" * 64}))
    assert lic.device_id() == "a" * 64
    state = lic.LicenseState.load()
    state.save()
    assert state.machine_id == lic._machine_id()
    monkeypatch.setattr(lic.platform, "node", lambda: "renamed")
    monkeypatch.setattr(lic.uuid, "getnode", lambda: 123)
    assert lic.device_bound(lic.LicenseState.load())
    calls = []
    monkeypatch.setattr(lic, "_post", lambda endpoint, payload: calls.append((endpoint, payload)) or {"status": "active"})
    assert lic.validate(lic.LicenseState.load())["status"] == "active"
    assert calls[0][0] == "validate"
    assert calls[0][1]["device_id"] == "a" * 64


def test_different_machine_remains_rejected(windows_state, monkeypatch):
    state = lic.LicenseState("token", "a" * 64)
    state.save()
    monkeypatch.setattr(lic, "_windows_machine_guid", lambda: "machine-B")
    assert not lic.device_bound(lic.LicenseState.load())
    with pytest.raises(lic.LicenseError):
        lic.validate(lic.LicenseState.load())


def test_unreadable_dpapi_token_is_never_reused(windows_state, monkeypatch):
    lic.LicenseState("token", "a" * 64).save()
    def cannot_decrypt(value):
        raise OSError("Wrong Windows user or device")
    monkeypatch.setattr(lic, "_dpapi_unprotect", cannot_decrypt)
    assert lic.LicenseState.load() is None
    assert lic.device_id() != "a" * 64
