"""Phase 0 online-update foundation: manifest, Ed25519, policy, version SSOT."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from nacl.signing import SigningKey

from app.core.constants import APP_VERSION, BASE_DIR
from app.core.update_manifest import (
    MANIFEST_SCHEMA,
    Artifact,
    ManifestError,
    UpdateManifest,
    canonical_json_bytes,
    dumps_manifest,
    parse_manifest,
    signing_payload_bytes,
)
from app.core.update_policy import (
    UpdatePolicyError,
    evaluate_update_eligibility,
    require_newer_version,
    verify_artifact_file,
    verify_artifact_size,
    verify_sha256_file,
)
from app.core.update_signing import (
    SigningError,
    VerificationError,
    load_signing_key_from_env,
    sign_manifest,
    verify_manifest_signature,
)
from app.core.update_trust import (
    VerificationKeyStore,
    packaged_private_key_paths,
    production_key_store,
)
from app.core.versioning import (
    VersionError,
    assert_version_sources_consistent,
    detect_version_drift,
    parse_semver,
)

# Deterministic test-only seed (never used as production trust material).
_TEST_SEED = bytes.fromhex("11" * 32)
_TEST_KEY_ID = "test-update-2026"
_OTHER_SEED = bytes.fromhex("22" * 32)


def _signing_key() -> SigningKey:
    return SigningKey(_TEST_SEED)


def _store_for(key: SigningKey, key_id: str = _TEST_KEY_ID) -> VerificationKeyStore:
    store = VerificationKeyStore()
    store.register(key_id, key.verify_key)
    return store


def _artifact(**overrides) -> dict:
    base = {
        "id": "setup",
        "kind": "installer",
        "filename": "JU-TAN-Office-Setup.exe",
        "size": 1024,
        "sha256": "a" * 64,
        "url": "https://ju-tan.com/download/JU-TAN-Office-Setup.exe",
    }
    base.update(overrides)
    return base


def _unsigned_dict(**overrides) -> dict:
    payload = {
        "schema": MANIFEST_SCHEMA,
        "channel": "gold",
        "product": "ju-tan-office",
        "version": "1.0.1",
        "min_version": "1.0.0",
        "published_at": "2026-09-20T10:00:00Z",
        "notes_sl": "Test",
        "notes_url": "https://ju-tan.com/download",
        "artifacts": [_artifact()],
    }
    payload.update(overrides)
    return payload


def _signed_manifest(**overrides) -> UpdateManifest:
    key = _signing_key()
    unsigned = parse_manifest(
        _unsigned_dict(**overrides),
        require_signature=False,
        require_https_artifacts=True,
    )
    return sign_manifest(unsigned, key, key_id=_TEST_KEY_ID)


def test_valid_manifest_roundtrip():
    signed = _signed_manifest()
    verified = verify_manifest_signature(signed, key_store=_store_for(_signing_key()))
    assert verified.version == "1.0.1"
    assert verified.signature is not None
    assert verified.signature.alg == "ed25519"


def test_malformed_manifest_json():
    with pytest.raises(ManifestError):
        parse_manifest("{not-json")


def test_unsupported_schema():
    with pytest.raises(ManifestError, match="Unsupported schema"):
        parse_manifest(_unsigned_dict(schema="other.v1"), require_signature=False)


def test_malformed_version():
    with pytest.raises(ManifestError, match="Malformed version"):
        parse_manifest(_unsigned_dict(version="1.0"), require_signature=False)


def test_unsafe_filename():
    with pytest.raises(ManifestError, match="Unsafe filename"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(filename="bad name.exe")]),
            require_signature=False,
        )


def test_path_traversal_filename():
    with pytest.raises(ManifestError, match="Path traversal"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(filename="../Setup.exe")]),
            require_signature=False,
        )


def test_non_https_url():
    with pytest.raises(ManifestError, match="Non-HTTPS"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(url="http://ju-tan.com/x.exe")]),
            require_signature=False,
        )


def test_invalid_sha256():
    with pytest.raises(ManifestError, match="Invalid SHA-256"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(sha256="xyz")]),
            require_signature=False,
        )


def test_non_positive_artifact_size():
    with pytest.raises(ManifestError, match="positive integer"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(size=0)]),
            require_signature=False,
        )
    with pytest.raises(ManifestError, match="positive integer"):
        parse_manifest(
            _unsigned_dict(artifacts=[_artifact(size=-5)]),
            require_signature=False,
        )


def test_wrong_artifact_size(tmp_path: Path):
    blob = tmp_path / "JU-TAN-Office-Setup.exe"
    blob.write_bytes(b"abc")
    art = Artifact(
        id="setup",
        kind="installer",
        filename=blob.name,
        size=999,
        sha256=hashlib.sha256(b"abc").hexdigest(),
        url="https://ju-tan.com/download/x.exe",
    )
    with pytest.raises(UpdatePolicyError, match="size mismatch"):
        verify_artifact_file(blob, art)


def test_valid_ed25519_signature():
    signed = _signed_manifest()
    verify_manifest_signature(signed, key_store=_store_for(_signing_key()))


def test_invalid_ed25519_signature():
    signed = _signed_manifest()
    other = SigningKey(_OTHER_SEED)
    with pytest.raises(VerificationError, match="Invalid Ed25519 signature"):
        verify_manifest_signature(signed, key_store=_store_for(other))


def test_tampered_manifest():
    signed = _signed_manifest()
    as_dict = signed.to_dict()
    as_dict["notes_sl"] = "TAMPERED"
    with pytest.raises(VerificationError):
        verify_manifest_signature(as_dict, key_store=_store_for(_signing_key()))


def test_unknown_key_id():
    signed = _signed_manifest()
    empty = VerificationKeyStore()
    with pytest.raises(VerificationError, match="Unknown key_id"):
        verify_manifest_signature(signed, key_store=empty)


def test_equal_version_rejection():
    with pytest.raises(UpdatePolicyError, match=r"(?i)equal version rejected"):
        require_newer_version("1.0.0", "1.0.0")


def test_downgrade_rejection():
    with pytest.raises(UpdatePolicyError, match=r"(?i)downgrade rejected"):
        require_newer_version("0.9.0", "1.0.0")


def test_newer_version_acceptance():
    require_newer_version("1.0.1", "1.0.0")
    signed = _signed_manifest(version="1.0.1", min_version="1.0.0")
    evaluate_update_eligibility(
        signed,
        current_version="1.0.0",
        key_store=_store_for(_signing_key()),
    )


def test_min_version_incompatibility():
    signed = _signed_manifest(version="2.0.0", min_version="1.5.0")
    with pytest.raises(UpdatePolicyError, match="min_version"):
        evaluate_update_eligibility(
            signed,
            current_version="1.0.0",
            key_store=_store_for(_signing_key()),
        )


def test_canonical_json_deterministic():
    payload = _unsigned_dict()
    a = canonical_json_bytes(payload)
    b = canonical_json_bytes(dict(reversed(list(payload.items()))))
    assert a == b
    assert b.decode("utf-8") == json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    signed = _signed_manifest()
    body = signing_payload_bytes(signed)
    assert b"signature" not in body


def test_version_source_drift_detection(tmp_path: Path):
    assert APP_VERSION == "1.0.0"
    assert_version_sources_consistent(BASE_DIR)
    assert detect_version_drift(BASE_DIR) == []

    # Synthetic drift in an isolated tree
    (tmp_path / "packaging").mkdir()
    (tmp_path / "Version.txt").write_text("Version: 9.9.9 GOLD\n", encoding="utf-8")
    (tmp_path / "packaging" / "Version.txt").write_text("Version: 1.0.0 GOLD\n", encoding="utf-8")
    (tmp_path / "packaging" / "file_version_info.txt").write_text(
        "StringStruct(u'FileVersion', u'1.0.0')\n"
        "StringStruct(u'ProductVersion', u'1.0.0')\n"
        "filevers=(1, 0, 0, 0)\nprodvers=(1, 0, 0, 0)\n",
        encoding="utf-8",
    )
    (tmp_path / "packaging" / "installer.iss").write_text(
        '#define MyAppVersion "1.0.0"\nVersionInfoVersion=1.0.0\n',
        encoding="utf-8",
    )
    # Monkeypatch: collect uses APP_VERSION from constants; drift vs Version.txt
    from app.core import versioning as versioning_mod

    problems = versioning_mod.detect_version_drift(tmp_path)
    assert any("Version.txt" in p for p in problems)
    with pytest.raises(VersionError):
        versioning_mod.assert_version_sources_consistent(tmp_path)


def test_release_generator_fails_without_signing_credentials(tmp_path: Path, monkeypatch):
    setup = tmp_path / "JU-TAN-Office-Setup.exe"
    setup.write_bytes(b"setup-bytes")
    monkeypatch.delenv("JU_TAN_UPDATE_SIGNING_KEY", raising=False)
    monkeypatch.delenv("JU_TAN_UPDATE_SIGNING_KEY_FILE", raising=False)
    script = BASE_DIR / "scripts" / "generate_update_manifest.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--setup",
            str(setup),
            "--artifact-url",
            "https://ju-tan.com/download/JU-TAN-Office-Setup.exe",
            "--key-id",
            "prod-2026",
            "--output",
            str(tmp_path / "latest.json"),
            "--skip-version-check",
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        env={k: v for k, v in __import__("os").environ.items() if not k.startswith("JU_TAN_UPDATE_SIGNING")},
    )
    assert result.returncode != 0
    assert "signing credentials missing" in (result.stderr + result.stdout).lower() or "missing" in (
        result.stderr + result.stdout
    ).lower()


def test_release_generator_signs_and_self_verifies(tmp_path: Path, monkeypatch):
    setup = tmp_path / "JU-TAN-Office-Setup.exe"
    setup.write_bytes(b"setup-bytes-for-manifest")
    key_file = tmp_path / "signing.seed"
    key_file.write_bytes(_TEST_SEED)
    monkeypatch.setenv("JU_TAN_UPDATE_SIGNING_KEY_FILE", str(key_file))
    out = tmp_path / "latest.json"
    script = BASE_DIR / "scripts" / "generate_update_manifest.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--setup",
            str(setup),
            "--artifact-url",
            "https://ju-tan.com/download/JU-TAN-Office-Setup.exe",
            "--key-id",
            _TEST_KEY_ID,
            "--output",
            str(out),
            "--version",
            "1.0.0",
            "--notes-sl",
            "test",
            "--skip-version-check",
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["signature"]["key_id"] == _TEST_KEY_ID
    parsed = parse_manifest(data, require_signature=True, require_https_artifacts=True)
    verify_manifest_signature(parsed, key_store=_store_for(_signing_key()))


def test_private_key_not_present_in_packaged_runtime_files():
    suspects = packaged_private_key_paths(BASE_DIR)
    assert suspects == []
    # Production directory must not contain private key material
    prod = BASE_DIR / "resources" / "update_keys" / "production"
    assert prod.is_dir()
    for path in prod.rglob("*"):
        if path.is_file():
            assert path.suffix.lower() not in {".key", ".pem", ".seed"}
            assert "private" not in path.name.lower()
            assert "secret" not in path.name.lower()


def test_production_store_does_not_silently_trust_test_keys():
    store = production_key_store(reload=True)
    assert _TEST_KEY_ID not in store
    signed = _signed_manifest()
    with pytest.raises(VerificationError, match="Unknown key_id"):
        verify_manifest_signature(signed, key_store=store)


def test_offline_latest_json_is_not_install_authorization():
    path = BASE_DIR / "updates" / "latest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == MANIFEST_SCHEMA
    assert data["channel"] == "dev"
    assert "signature" not in data
    # Empty artifact URL — not a working production download.
    assert data["artifacts"][0]["url"] == ""
    # Must not evaluate as a production-eligible update.
    manifest = parse_manifest(data, require_signature=False, require_https_artifacts=False)
    with pytest.raises(UpdatePolicyError):
        evaluate_update_eligibility(
            manifest,
            current_version="0.9.0",
            verify_signature=True,
            key_store=production_key_store(reload=True),
        )


def test_load_signing_key_from_env_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "key.seed"
    path.write_bytes(_TEST_SEED)
    monkeypatch.setenv("JU_TAN_UPDATE_SIGNING_KEY_FILE", str(path))
    monkeypatch.delenv("JU_TAN_UPDATE_SIGNING_KEY", raising=False)
    key = load_signing_key_from_env()
    assert bytes(key) == bytes(_signing_key())


def test_sha256_file_ok(tmp_path: Path):
    blob = tmp_path / "JU-TAN-Office-Setup.exe"
    content = b"hello-update"
    blob.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    assert verify_sha256_file(blob, digest) == digest
    verify_artifact_size(blob, len(content))


def test_parse_semver_strict():
    assert parse_semver("1.0.0") == (1, 0, 0)
    with pytest.raises(VersionError):
        parse_semver("1.0.0-GOLD")


def test_dumps_manifest_includes_signature():
    signed = _signed_manifest()
    text = dumps_manifest(signed)
    assert '"signature"' in text
    assert _TEST_KEY_ID in text
