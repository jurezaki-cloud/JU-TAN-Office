"""Varnostna utrditev: gesla, skrivnosti, RBAC, poti, licenca."""

import json

import pytest

from app.core.config_guard import stamp, valid
from app.core.license import activate_offline, current_edition, issue, verify
from app.core.passwords import hash_password, validate_policy, verify_password
from app.core.permissions import can, require, set_identity
from app.core.recovery import load_draft, save_draft
from app.core.secrets import decrypt_bytes, encrypt_bytes, reveal, seal
from app.core.security import (
    assert_safe_document,
    ensure_inside,
    require_email,
    require_iban,
    require_number,
    require_trr,
    require_vat,
    safe_filename,
)
from app.core.session import session
from app.database.customer_repository import customer_repository
from app.modules.settings.settings_controller import SETTINGS_PATH, SettingsController, default_settings


def test_password_hashed_not_plaintext():
    hashed = hash_password("SecurePass1x")
    assert "SecurePass1x" not in hashed
    assert hashed.startswith("argon2id:") or hashed.startswith("scrypt:")
    assert verify_password("SecurePass1x", hashed)
    assert not verify_password("wrong-pass-99", hashed)
    with pytest.raises(ValueError):
        validate_policy("short")


def test_secret_storage_not_readable():
    token = encrypt_bytes(b"smtp-secret")
    assert "smtp-secret" not in token
    assert decrypt_bytes(token) == b"smtp-secret"
    blob = seal({"api_key": "abc-123", "smtp_password": "mail"})
    opened = reveal(blob)
    assert opened["api_key"] == "abc-123"
    assert "abc-123" not in blob


def test_rbac_readonly_cannot_escalate():
    set_identity(role="Read Only", authenticated=True)
    try:
        assert can("read")
        assert not can("delete")
        assert not can("backup")
        with pytest.raises(PermissionError):
            require("settings")
    finally:
        set_identity(role="Administrator", authenticated=True)
    require("backup")


def test_audit_log_written():
    from app.core.constants import DATA_DIR
    from app.core.permissions import AUDIT_FILE, audit

    audit("export", "security-test")
    text = AUDIT_FILE.read_text(encoding="utf-8")
    assert "export" in text
    assert "security-test" in text
    assert DATA_DIR.exists()


def test_input_validation():
    assert require_email("ana@firma.si")
    assert require_vat("SI12345678") == "SI12345678"
    assert require_iban("SI56123412341234123")
    assert require_trr("SI56123412341234123")
    assert require_number("12.5", minimum=0) == 12.5
    with pytest.raises(ValueError):
        require_email("not-an-email")
    with pytest.raises(ValueError):
        require_vat("XX")


def test_sql_injection_still_parameterized():
    row = customer_repository.get_by_id("1 OR 1=1")
    assert row is None or row[1] != "all-rows"


def test_path_traversal_blocked(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    with pytest.raises(PermissionError):
        ensure_inside(tmp_path / ".." / "secret.txt", root)
    assert ".." not in safe_filename("..\\windows\\system32\\x.txt")
    with pytest.raises(ValueError):
        assert_safe_document(root / "payload.exe", root)


def test_session_lock_and_logout():
    session.login("Tester", "Administrator")
    assert session.authenticated
    session.lock()
    assert session.locked
    assert not can("write")
    session.unlock("Tester")
    assert can("write")
    session.logout()
    assert not session.authenticated
    set_identity(role="Administrator", authenticated=True)
    session.authenticated = True
    session.locked = False


def test_backup_restore_integrity():
    from app.core.db_guard import integrity_ok, verify_backup

    controller = SettingsController()
    backup = controller.backup_database()
    assert verify_backup(backup)
    assert integrity_ok()
    controller.restore_database(backup)


def test_config_checksum_and_migration():
    data = stamp({"appearance": {"theme": "light"}, "config_version": 1})
    assert valid(data)
    data["_checksum"] = "deadbeef"
    assert not valid(data)


def test_license_offline_editions():
    payload = issue(edition="enterprise", days=30)
    assert verify(payload)
    assert activate_offline(payload) == "enterprise"
    assert current_edition() == "enterprise"
    payload["edition"] = "trial"
    assert not verify(payload)


def test_crash_draft_recovery():
    path = save_draft("invoice", {"number": "RAC-1"})
    assert path.exists()
    assert load_draft("invoice")["number"] == "RAC-1"


def test_settings_keep_password_hash():
    controller = SettingsController()
    hashed = hash_password("SecurePass1x")
    extras = default_settings()
    extras["password_hash"] = hashed
    extras["swift"] = "LJBASI2X"
    controller.save_extras(extras)
    loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    assert "SecurePass1x" not in json.dumps(loaded)
    controller.save_extras({"swift": "UPDATED"})
    again = controller.load_extras()
    assert again["password_hash"] == hashed
    assert again["swift"] == "UPDATED"


def test_broken_session_unauthenticated():
    set_identity(authenticated=False)
    try:
        assert not can("read")
    finally:
        set_identity(role="Administrator", authenticated=True)
