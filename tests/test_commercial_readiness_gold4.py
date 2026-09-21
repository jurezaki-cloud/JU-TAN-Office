"""GOLD-4 commercial readiness — license bind, update manifest, installer contracts."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest

from app.core.update import (
    UpdateError,
    canonical_manifest,
    is_newer,
    validate_manifest,
    verify_manifest_signature,
)
from app.services import licensing_service as lic


ROOT = Path(__file__).resolve().parent.parent


def test_license_api_requires_https(monkeypatch):
    monkeypatch.setattr(lic, "API_BASE", "http://evil.example/api")
    monkeypatch.delenv("JU_TAN_LICENSE_INSECURE", raising=False)
    with pytest.raises(lic.LicenseError, match="HTTPS"):
        lic.ensure_api_base()


def test_license_api_allows_localhost_insecure(monkeypatch):
    monkeypatch.setattr(lic, "API_BASE", "http://127.0.0.1:8080/api")
    monkeypatch.setenv("JU_TAN_LICENSE_INSECURE", "1")
    assert lic.ensure_api_base().startswith("http://127.0.0.1")


def test_license_key_normalization_rejects_short():
    with pytest.raises(lic.LicenseError):
        lic._normalize_license_key("ABC")


def test_device_bound_compare(monkeypatch):
    monkeypatch.setattr(lic, "device_id", lambda: "a" * 64)
    state = lic.LicenseState(activation_token="t", device_id="a" * 64)
    assert lic.device_bound(state) is True
    state.device_id = "b" * 64
    assert lic.device_bound(state) is False


def test_validate_rejects_device_mismatch(monkeypatch):
    monkeypatch.setattr(lic, "device_id", lambda: "a" * 64)
    state = lic.LicenseState(activation_token="tok", device_id="b" * 64)
    with pytest.raises(lic.LicenseError, match="napravo"):
        lic.validate(state)


def test_manifest_requires_https_and_sha_when_url_set():
    with pytest.raises(UpdateError, match="HTTPS"):
        validate_manifest({"version": "1.0.1", "url": "http://example.com/x.exe", "sha256": "a" * 64})
    with pytest.raises(UpdateError, match="SHA-256"):
        validate_manifest({"version": "1.0.1", "url": "https://example.com/x.exe", "sha256": "dead"})


def test_manifest_signature_roundtrip(monkeypatch, tmp_path):
    key = bytes.fromhex("11" * 32)
    monkeypatch.setenv("JU_TAN_UPDATE_HMAC_KEY", key.hex())
    payload = {
        "version": "1.0.1",
        "notes": "test",
        "url": "https://example.com/JU-TAN-Office-Setup.exe",
        "sha256": "ab" * 32,
        "channel": "GOLD",
    }
    payload["signature"] = hmac.new(key, canonical_manifest(payload), hashlib.sha256).hexdigest()
    assert verify_manifest_signature(payload) is True
    assert validate_manifest(payload)["version"] == "1.0.1"

    bad = dict(payload)
    bad["signature"] = "00" * 32
    with pytest.raises(UpdateError, match="Podpis"):
        validate_manifest(bad)


def test_manifest_require_signature_flag(monkeypatch):
    monkeypatch.setenv("JU_TAN_UPDATE_REQUIRE_SIGNATURE", "1")
    with pytest.raises(UpdateError, match="podpisan"):
        validate_manifest(
            {
                "version": "1.0.1",
                "url": "https://example.com/setup.exe",
                "sha256": "cd" * 32,
            }
        )


def test_is_newer_semver():
    assert is_newer("1.0.1", "1.0.0")
    assert not is_newer("1.0.0", "1.0.0")


def test_bundled_latest_json_schema():
    data = json.loads((ROOT / "updates" / "latest.json").read_text(encoding="utf-8"))
    assert "version" in data
    assert "sha256" in data
    assert "signature" in data
    assert "channel" in data
    url = str(data.get("url") or "")
    if url:
        assert url.lower().startswith("https://")


def test_update_keys_and_scripts_present():
    assert (ROOT / "resources" / "update_keys" / "production" / "manifest_hmac.hex").is_file()
    assert (ROOT / "scripts" / "sign_update_manifest.ps1").is_file()
    assert (ROOT / "scripts" / "check_installer_production.ps1").is_file()
    assert (ROOT / "docs" / "GOLD4_COMMERCIAL_READINESS.md").is_file()


def test_licensing_uses_constants_version():
    from app.core.constants import APP_VERSION

    src = (ROOT / "app" / "services" / "licensing_service.py").read_text(encoding="utf-8")
    assert "from app.core.constants import APP_VERSION" in src
    assert 'APP_VERSION = "1.0.0"' not in src
    assert APP_VERSION


def test_license_gate_checks_device_bind():
    src = (ROOT / "app" / "services" / "license_gate.py").read_text(encoding="utf-8")
    assert "device_bound" in src
    assert "clear_license_state" in src


def test_installer_production_script_covers_mutex_and_signing():
    text = (ROOT / "scripts" / "check_installer_production.ps1").read_text(encoding="utf-8")
    assert "AppMutex=JU-TANOfficeMutex" in text
    assert "RequireSignedArtifacts" in text
    assert "manifest_hmac.hex" in text
