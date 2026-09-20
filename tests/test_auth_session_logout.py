"""Auth/session gates: remember-user must not bypass password; logout must clear session."""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from app.core.auth_gate import (
    AUTH_ERROR_MESSAGE,
    authenticate_credentials,
    logout_requires_reauth,
    needs_credential_onboarding,
    password_is_configured,
    startup_requires_authentication,
)
from app.core.config_guard import stamp
from app.core.passwords import hash_password
from app.core.session import session
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import (
    SETTINGS_PATH,
    SettingsController,
    default_settings,
)
from app.modules.settings.settings_page import SettingsPage


VALID_PASSWORD = "SecurePass1x"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


@pytest.fixture(autouse=True)
def _restore_session():
    """Do not leave the process unauthenticated or settings poisoned for later tests."""
    from app.core.permissions import set_identity

    _wipe_users()
    yield
    _wipe_users()
    session.login("Administrator", "Administrator")
    set_identity(user="Administrator", role="Administrator", authenticated=True)
    session.locked = False
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()


def _write_extras(**overrides) -> dict:
    data = default_settings()
    data.update(overrides)
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(stamp(data), ensure_ascii=False), encoding="utf-8")
    return SettingsController().load_extras()


def _logout_host(qt_app) -> QWidget:
    host = QWidget()
    host.controller = SettingsController()
    host._logout = SettingsPage._logout.__get__(host, SettingsPage)
    return host


def test_remember_user_with_password_still_requires_startup_auth():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(password_hash=hashed, remember_user=True, administrator="Admin")
    assert password_is_configured(extras) is True
    assert startup_requires_authentication(extras) is True
    assert logout_requires_reauth(extras) is True
    extras_off = dict(extras)
    extras_off["remember_user"] = False
    assert startup_requires_authentication(extras_off) is True


def test_no_password_requires_credential_onboarding_not_auto_login():
    extras = _write_extras(
        password_hash="",
        remember_user=True,
        setup_complete=True,
        administrator="Administrator",
    )
    assert password_is_configured(extras) is False
    assert startup_requires_authentication(extras) is False
    assert needs_credential_onboarding(extras) is True
    assert logout_requires_reauth(extras) is False


def test_onboarding_not_needed_when_credentials_exist():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        password_hash=hashed,
        setup_complete=True,
        administrator="Admin",
    )
    assert needs_credential_onboarding(extras) is False
    assert startup_requires_authentication(extras) is True


def test_onboarding_not_needed_before_setup_complete():
    extras = _write_extras(password_hash="", setup_complete=False)
    assert needs_credential_onboarding(extras) is False


def test_restart_always_requires_login_when_password_configured():
    hashed = hash_password(VALID_PASSWORD)
    with_pwd = _write_extras(password_hash=hashed, remember_user=True)
    assert startup_requires_authentication(with_pwd) is True
    session.logout()
    assert session.authenticated is False
    assert startup_requires_authentication(SettingsController().load_extras()) is True


def test_logout_with_password_requires_reauth_dialog(qt_app, monkeypatch):
    hashed = hash_password(VALID_PASSWORD)
    _write_extras(password_hash=hashed, remember_user=True)
    session.login("Administrator", "Administrator")
    assert session.authenticated

    host = _logout_host(qt_app)
    shown = {"unlock": False}
    quit_calls = []

    class _FakeUnlock:
        def __init__(self, parent=None):
            shown["unlock"] = True

        def exec(self):
            from PySide6.QtWidgets import QDialog

            session.login("Administrator", "Administrator")
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.windows.unlock_dialog.UnlockDialog", _FakeUnlock)
    monkeypatch.setattr(QApplication, "quit", lambda: quit_calls.append(1))

    host._logout()
    assert shown["unlock"] is True
    assert session.authenticated is True
    assert not quit_calls
    host.close()
    host.deleteLater()


def test_logout_without_password_clears_session_and_quits(qt_app, monkeypatch):
    _write_extras(password_hash="", remember_user=True)
    session.login("Administrator", "Administrator")
    assert session.authenticated

    host = _logout_host(qt_app)
    quit_calls = []
    monkeypatch.setattr(QApplication, "quit", lambda: quit_calls.append(1))

    host._logout()
    assert session.authenticated is False
    assert session.locked is True
    assert quit_calls, "Odjava without password must end the process"
    host.close()
    host.deleteLater()


def test_logout_with_password_cancel_quits(qt_app, monkeypatch):
    hashed = hash_password(VALID_PASSWORD)
    _write_extras(password_hash=hashed, remember_user=False)
    session.login("Administrator", "Administrator")

    host = _logout_host(qt_app)
    quit_calls = []

    class _CancelUnlock:
        def __init__(self, parent=None):
            pass

        def exec(self):
            from PySide6.QtWidgets import QDialog

            return QDialog.DialogCode.Rejected

    monkeypatch.setattr("app.windows.unlock_dialog.UnlockDialog", _CancelUnlock)
    monkeypatch.setattr(QApplication, "quit", lambda: quit_calls.append(1))

    host._logout()
    assert session.authenticated is False
    assert quit_calls
    host.close()
    host.deleteLater()


def test_authenticate_credentials_valid():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        password_hash=hashed,
        administrator="jurez",
        role="Administrator",
        account_enabled=True,
    )
    ok, err = authenticate_credentials("jurez", VALID_PASSWORD, extras)
    assert ok is True
    assert err is None


def test_authenticate_wrong_username_generic_error():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(password_hash=hashed, administrator="jurez")
    ok, err = authenticate_credentials("other", VALID_PASSWORD, extras)
    assert ok is False
    assert err == AUTH_ERROR_MESSAGE


def test_authenticate_wrong_password_generic_error():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(password_hash=hashed, administrator="jurez")
    ok, err = authenticate_credentials("jurez", "WrongPass99", extras)
    assert ok is False
    assert err == AUTH_ERROR_MESSAGE


def test_authenticate_disabled_account_rejected():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        password_hash=hashed,
        administrator="jurez",
        account_enabled=False,
    )
    ok, err = authenticate_credentials("jurez", VALID_PASSWORD, extras)
    assert ok is False
    assert err == AUTH_ERROR_MESSAGE


def test_authenticate_empty_password_rejected():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(password_hash=hashed, administrator="jurez")
    ok, err = authenticate_credentials("jurez", "", extras)
    assert ok is False


def test_authenticate_empty_username_rejected():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(password_hash=hashed, administrator="jurez")
    ok, err = authenticate_credentials("", VALID_PASSWORD, extras)
    assert ok is False


def test_remember_username_does_not_bypass_password():
    hashed = hash_password(VALID_PASSWORD)
    extras = _write_extras(
        password_hash=hashed,
        remember_user=True,
        administrator="Admin",
    )
    assert startup_requires_authentication(extras) is True
    ok, _ = authenticate_credentials("Admin", "", extras)
    assert ok is False
