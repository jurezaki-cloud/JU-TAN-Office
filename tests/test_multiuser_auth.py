"""Multi-user SQLite auth, RBAC, migration, Fresh reset (isolated temp data)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from app.core.auth_gate import (
    AUTH_ERROR_MESSAGE,
    authenticate_credentials,
    ensure_auth_migrated,
    needs_credential_onboarding,
    password_is_configured,
    startup_requires_authentication,
)
from app.core.config_guard import stamp
from app.core.db_guard import integrity_ok
from app.core.fresh_reset import FRESH_CONFIRM_TEXT, FreshResetError, FreshResetService
from app.core.passwords import hash_password, verify_password
from app.core.permissions import can, can_open_page, set_identity
from app.core.session import session
from app.core.user_service import (
    LastAdminError,
    apply_session_for_user,
    create_first_administrator,
    create_user,
    reset_user_password,
    role_default_permission_keys,
    update_user,
    users_exist,
)
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import (
    SETTINGS_PATH,
    SettingsController,
    default_settings,
)

VALID_PASSWORD = "SecurePass1x"
VALID_PASSWORD_2 = "SecurePass2y"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


@pytest.fixture(autouse=True)
def _clean_users():
    _wipe_users()
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()
    session.login("Administrator", "Administrator")
    session.locked = False
    yield
    _wipe_users()
    session.login("Administrator", "Administrator")
    session.locked = False
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()


def _write_extras(**overrides) -> dict:
    data = default_settings()
    data.update(overrides)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(stamp(data), ensure_ascii=False), encoding="utf-8")
    return SettingsController().load_extras()


def test_first_account_custom_username_admin():
    assert users_exist() is False
    user = create_first_administrator("Jure", VALID_PASSWORD)
    assert user["username"] == "Jure"
    assert user["role"] == "Administrator"
    assert user["is_active"] is True
    assert verify_password(VALID_PASSWORD, user["password_hash"])
    assert VALID_PASSWORD not in user["password_hash"]
    keys = user_repository.get_permissions(user["id"])
    assert "users" in keys and "fresh" in keys and "settings" in keys
    assert users_exist() is True
    with pytest.raises(PermissionError):
        create_first_administrator("Other", VALID_PASSWORD)


def test_first_account_password_rules():
    with pytest.raises(ValueError):
        create_first_administrator("Jure", "short")
    with pytest.raises(ValueError):
        create_first_administrator("", VALID_PASSWORD)


def test_username_normalized_unique():
    create_first_administrator("Jure", VALID_PASSWORD)
    session.login("Jure", "Administrator", user_id=1)
    apply_session_for_user(user_repository.get_by_username("Jure"))
    with pytest.raises(ValueError, match="že obstaja"):
        create_user(username="jure", password=VALID_PASSWORD_2, role="Sales")
    with pytest.raises(ValueError, match="že obstaja"):
        create_user(username="JURE", password=VALID_PASSWORD_2, role="Sales")


def test_login_sqlite_and_generic_errors():
    create_first_administrator("Jure", VALID_PASSWORD)
    ok, err = authenticate_credentials("Jure", VALID_PASSWORD, {})
    assert ok and err is None
    ok, err = authenticate_credentials("Jure", "WrongPass1x", {})
    assert not ok and err == AUTH_ERROR_MESSAGE
    ok, err = authenticate_credentials("Nobody", VALID_PASSWORD, {})
    assert not ok and err == AUTH_ERROR_MESSAGE


def test_inactive_user_rejected():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    other = create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
    update_user(other["id"], is_active=False)
    ok, _ = authenticate_credentials("Tanja", VALID_PASSWORD_2, {})
    assert not ok


def test_second_user_not_auto_admin():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    tanja = create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
    assert tanja["role"] == "Sales"
    assert "users" not in user_repository.get_permissions(tanja["id"])
    apply_session_for_user(tanja)
    assert can("users") is False
    assert can("read") is True
    assert can_open_page(1) is True  # invoices in Sales
    assert can_open_page(8) is False  # settings


def test_permission_switch_no_leak():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    tanja = create_user(username="Tanja", password=VALID_PASSWORD_2, role="Read Only")
    apply_session_for_user(tanja)
    assert can("write") is False
    apply_session_for_user(admin)
    assert can("users") is True
    assert can("fresh") is True


def test_last_admin_protection():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    with pytest.raises(LastAdminError):
        update_user(admin["id"], is_active=False)
    with pytest.raises(LastAdminError):
        update_user(admin["id"], role="Sales", permissions=role_default_permission_keys("Sales"))


def test_password_reset():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    tanja = create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
    reset_user_password(tanja["id"], "BrandNew99x")
    ok, _ = authenticate_credentials("Tanja", VALID_PASSWORD_2, {})
    assert not ok
    ok, _ = authenticate_credentials("Tanja", "BrandNew99x", {})
    assert ok


def test_legacy_migration_preserves_hash_and_clears_settings():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        setup_complete=True,
        password_hash=hashed,
        administrator="LegacyBoss",
        role="Administrator",
        account_enabled=True,
    )
    assert users_exist() is False
    migrated = ensure_auth_migrated(extras)
    assert users_exist() is True
    user = user_repository.get_by_username("LegacyBoss")
    assert user is not None
    assert user["password_hash"] == hashed
    assert migrated.get("password_hash") == ""
    assert migrated.get("legacy_auth_migrated") is True
    # Idempotent
    again = ensure_auth_migrated(migrated)
    assert user_repository.count_users() == 1
    assert again.get("password_hash") == ""
    ok, _ = authenticate_credentials("LegacyBoss", VALID_PASSWORD, migrated)
    assert ok


def test_legacy_no_password_needs_onboarding():
    extras = _write_extras(setup_complete=True, password_hash="")
    assert needs_credential_onboarding(extras) is True
    assert users_exist() is False


def test_password_is_configured_via_users():
    create_first_administrator("Jure", VALID_PASSWORD)
    assert password_is_configured({}) is True
    assert startup_requires_authentication({}) is True


def test_fresh_reset_on_isolated_service(tmp_path):
    """Fresh uses explicit data/backup dirs; never touches ProgramData."""
    data = tmp_path / "data"
    backup = tmp_path / "backup"
    data.mkdir()
    backup.mkdir()
    db_path = data / "ju_tan.db"

    # Build a minimal DB via the app's Database pointing temporarily at db_path
    from app.database import database as database_mod

    previous = database_mod.db.database
    database_mod.db.dispose()
    database_mod.db.database = db_path
    try:
        database_mod.db.initialize()
        _wipe_users()
        admin = create_first_administrator("Jure", VALID_PASSWORD)
        apply_session_for_user(admin)

        # Seed business row
        conn = database_mod.db.connect()
        conn.execute("INSERT INTO customers(company) VALUES ('Acme')")
        conn.commit()
        conn.close()

        settings = {
            **default_settings(),
            "setup_complete": True,
            "administrator": "Jure",
            "remember_user": True,
            "remembered_username": "Jure",
            "password_hash": "",
            "legacy_auth_migrated": True,
        }
        (data / "settings.json").write_text(
            json.dumps(stamp(settings), ensure_ascii=False), encoding="utf-8"
        )
        (data / "warehouse.json").write_text("{}", encoding="utf-8")
        (data / "company_logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (data / "logo.png").write_bytes(b"BRAND")
        docs = data / "documents"
        docs.mkdir()
        (docs / "file.txt").write_text("doc", encoding="utf-8")

        service = FreshResetService(data_dir=data, backup_dir=backup)
        service.database_path = db_path

        set_identity(
            role="Sales",
            authenticated=True,
            actions=frozenset({"read", "write"}),
            clear_overrides=True,
        )
        with pytest.raises(PermissionError):
            service.assert_authorized()

        apply_session_for_user(admin)
        with pytest.raises(FreshResetError):
            service.execute(password=VALID_PASSWORD, confirm_text="fresh")
        with pytest.raises(PermissionError):
            service.execute(password="WrongPass1x", confirm_text=FRESH_CONFIRM_TEXT)

        backup_path = service.execute(password=VALID_PASSWORD, confirm_text=FRESH_CONFIRM_TEXT)
        assert backup_path.is_dir()
        assert (backup_path / "ju_tan.db").is_file()
        assert integrity_ok(db_path)
        assert user_repository.count_users() == 0
        assert not (data / "warehouse.json").exists()
        assert not (data / "company_logo.png").exists()
        assert (data / "logo.png").read_bytes() == b"BRAND"
        settings_after = json.loads((data / "settings.json").read_text(encoding="utf-8"))
        assert settings_after.get("setup_complete") is False
        assert settings_after.get("remember_user") is False
        assert session.authenticated is False
        # Backup still has pre-reset customer
        import sqlite3

        bconn = sqlite3.connect(backup_path / "ju_tan.db")
        assert bconn.execute("SELECT company FROM customers").fetchone()[0] == "Acme"
        bconn.close()
    finally:
        database_mod.db.dispose()
        database_mod.db.database = previous
        database_mod.db.initialize()
        _wipe_users()
        session.login("Administrator", "Administrator")


def test_credential_onboarding_creates_sqlite_user(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    _write_extras(setup_complete=True, password_hash="", administrator="Administrator")
    from app.windows.credential_onboarding_dialog import CredentialOnboardingDialog

    dlg = CredentialOnboardingDialog()
    assert dlg.user.text() == ""  # forced Administrator username not prefilled
    dlg.user.setText("Jure")
    dlg.password.setText(VALID_PASSWORD)
    dlg.password2.setText(VALID_PASSWORD)
    dlg._save()
    dlg.close()
    assert users_exist()
    user = user_repository.get_by_username("Jure")
    assert user["role"] == "Administrator"
    extras = SettingsController().load_extras()
    assert extras.get("password_hash") in ("", None)
    assert needs_credential_onboarding(extras) is False


def test_first_run_creates_sqlite_admin(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(
        "app.windows.first_run_wizard.company_repository.save",
        lambda *a, **k: None,
    )
    from app.windows.first_run_wizard import FirstRunWizard

    wizard = FirstRunWizard()
    assert wizard.admin.text() == ""
    wizard.company.setText("ACME d.o.o.")
    wizard.admin.setText("boss")
    wizard.password.setText(VALID_PASSWORD)
    wizard.password2.setText(VALID_PASSWORD)
    wizard._finish()
    assert users_exist()
    user = user_repository.get_by_username("boss")
    assert user["role"] == "Administrator"
    extras = SettingsController().load_extras()
    assert extras["setup_complete"] is True
    assert extras.get("password_hash") in ("", None)
    wizard.close()
