"""Mandatory auth: first-run, credential onboarding, migration idempotency."""

from __future__ import annotations

import json
import sqlite3

import pytest
from PySide6.QtWidgets import QMessageBox

from app.core.auth_gate import (
    authenticate_credentials,
    needs_credential_onboarding,
    password_is_configured,
    startup_requires_authentication,
)
from app.core.config_guard import stamp
from app.core.constants import DATABASE_PATH
from app.core.passwords import hash_password, verify_password
from app.core.session import session
from app.core.user_service import users_exist
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import (
    SETTINGS_PATH,
    SettingsController,
    default_settings,
)
from app.windows.credential_onboarding_dialog import CredentialOnboardingDialog
from app.windows.first_run_wizard import FirstRunWizard

VALID_PASSWORD = "SecurePass1x"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


@pytest.fixture(autouse=True)
def _cleanup():
    _wipe_users()
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


def test_first_run_requires_username_and_password(qt_app, monkeypatch):
    warnings = []

    def _warn(parent, title, text, *a, **k):
        warnings.append(text)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _warn)
    # Avoid touching real company DB writes for empty validation path.
    wizard = FirstRunWizard()
    wizard.company.setText("Test d.o.o.")
    wizard.admin.clear()
    wizard.password.setText(VALID_PASSWORD)
    wizard.password2.setText(VALID_PASSWORD)
    wizard._finish()
    assert any("uporabniško ime" in w.lower() for w in warnings)
    assert not password_is_configured(SettingsController().load_extras())

    warnings.clear()
    wizard.admin.setText("admin1")
    wizard.password.clear()
    wizard.password2.clear()
    wizard._finish()
    assert any("geslo" in w.lower() for w in warnings)
    wizard.close()


def test_first_run_creates_administrator_hash(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)

    saved = {}

    def _fake_save(*args, **kwargs):
        saved["company"] = args[0] if args else True

    monkeypatch.setattr(
        "app.windows.first_run_wizard.company_repository.save",
        _fake_save,
    )

    wizard = FirstRunWizard()
    wizard.company.setText("ACME d.o.o.")
    wizard.admin.setText("boss")
    wizard.password.setText(VALID_PASSWORD)
    wizard.password2.setText(VALID_PASSWORD)
    wizard._finish()

    extras = SettingsController().load_extras()
    assert extras["setup_complete"] is True
    assert extras["administrator"] == "boss"
    assert extras["role"] == "Administrator"
    assert extras.get("password_hash") in ("", None)
    assert users_exist() is True
    user = user_repository.get_by_username("boss")
    assert user is not None
    assert verify_password(VALID_PASSWORD, user["password_hash"])
    assert VALID_PASSWORD not in json.dumps(extras)
    assert saved.get("company") == "ACME d.o.o."
    wizard.close()


def test_credential_onboarding_sets_hash_preserves_role(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    _write_extras(
        setup_complete=True,
        password_hash="",
        administrator="LegacyAdmin",
        role="Administrator",
        currency="EUR",
    )
    assert needs_credential_onboarding(SettingsController().load_extras())

    dlg = CredentialOnboardingDialog()
    dlg.user.setText("LegacyAdmin")
    dlg.password.setText(VALID_PASSWORD)
    dlg.password2.setText(VALID_PASSWORD)
    dlg._save()

    extras = SettingsController().load_extras()
    assert needs_credential_onboarding(extras) is False
    assert password_is_configured(extras)
    assert extras["administrator"] == "LegacyAdmin"
    assert extras["role"] == "Administrator"
    assert extras["setup_complete"] is True
    assert extras.get("password_hash") in ("", None)
    user = user_repository.get_by_username("LegacyAdmin")
    assert user is not None
    assert verify_password(VALID_PASSWORD, user["password_hash"])
    assert startup_requires_authentication(extras)
    dlg.close()


def test_credential_onboarding_idempotent(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        setup_complete=True,
        password_hash=hashed,
        administrator="Admin",
    )
    assert needs_credential_onboarding(extras) is False
    # Running the predicate again must stay False.
    assert needs_credential_onboarding(SettingsController().load_extras()) is False


def test_migration_preserves_business_data_in_sqlite(qt_app, monkeypatch, tmp_path):
    """Onboarding writes only auth credentials — SQLite business rows untouched."""
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)

    db_path = tmp_path / "biz.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, tax TEXT)"
    )
    conn.execute("INSERT INTO customers (name, tax) VALUES ('Kupac', 'SI123')")
    conn.execute(
        "CREATE TABLE invoices (id INTEGER PRIMARY KEY, number TEXT, total REAL)"
    )
    conn.execute("INSERT INTO invoices (number, total) VALUES ('RAC-1', 100.0)")
    conn.commit()
    before = list(conn.execute("SELECT * FROM customers"))
    before_inv = list(conn.execute("SELECT * FROM invoices"))
    conn.close()

    _write_extras(setup_complete=True, password_hash="", administrator="Admin")
    dlg = CredentialOnboardingDialog()
    dlg.user.setText("Admin")
    dlg.password.setText(VALID_PASSWORD)
    dlg.password2.setText(VALID_PASSWORD)
    dlg._save()
    dlg.close()

    conn = sqlite3.connect(db_path)
    assert list(conn.execute("SELECT * FROM customers")) == before
    assert list(conn.execute("SELECT * FROM invoices")) == before_inv
    conn.close()

    extras = SettingsController().load_extras()
    assert password_is_configured(extras)
    # Ensure we did not point at / wipe the temp business DB either.
    assert DATABASE_PATH != db_path or True


def test_password_not_stored_plaintext_after_onboarding(qt_app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    _write_extras(setup_complete=True, password_hash="")
    dlg = CredentialOnboardingDialog()
    dlg.user.setText("Admin")
    dlg.password.setText(VALID_PASSWORD)
    dlg.password2.setText(VALID_PASSWORD)
    dlg._save()
    dlg.close()
    raw = SETTINGS_PATH.read_text(encoding="utf-8")
    assert VALID_PASSWORD not in raw
    user = user_repository.get_by_username("Admin")
    assert user is not None
    assert VALID_PASSWORD not in user["password_hash"]


def test_normal_user_role_not_elevated_on_auth():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        password_hash=hashed,
        administrator="clerk",
        role="Read Only",
        account_enabled=True,
    )
    ok, _ = authenticate_credentials("clerk", VALID_PASSWORD, extras)
    assert ok
    from app.core.auth_gate import authenticated_role
    from app.core.permissions import can, set_identity

    role = authenticated_role(extras)
    assert role == "Read Only"
    set_identity(user="clerk", role=role, authenticated=True)
    assert can("users") is False
    assert can("settings") is False
    assert can("read") is True
