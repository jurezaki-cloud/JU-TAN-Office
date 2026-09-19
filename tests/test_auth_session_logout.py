"""Auth/session gates: remember-user must not bypass password; logout must clear session."""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from app.core.auth_gate import (
    logout_requires_reauth,
    password_is_configured,
    startup_requires_authentication,
)
from app.core.config_guard import stamp
from app.core.passwords import hash_password
from app.core.session import session
from app.modules.settings.settings_controller import (
    SETTINGS_PATH,
    SettingsController,
    default_settings,
)
from app.modules.settings.settings_page import SettingsPage


VALID_PASSWORD = "SecurePass1x"


@pytest.fixture(autouse=True)
def _restore_session():
    """Do not leave the process unauthenticated or settings poisoned for later tests."""
    from app.core.permissions import set_identity

    yield
    session.login("Administrator", "Administrator")
    set_identity(user="Administrator", role="Administrator", authenticated=True)
    session.locked = False
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()


def _write_extras(**overrides) -> dict:
    data = default_settings()
    data.update(overrides)
    # Do not force setup_complete — other tests assert first-run gates on shared DATA_DIR.
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(stamp(data), ensure_ascii=False), encoding="utf-8")
    return SettingsController().load_extras()


def _logout_host(qt_app) -> QWidget:
    """Minimal QWidget host for SettingsPage._logout without building SettingsPage."""
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
    # remember_user is username UX only — gate ignores it
    extras_off = dict(extras)
    extras_off["remember_user"] = False
    assert startup_requires_authentication(extras_off) is True


def test_no_password_first_run_style_skips_startup_unlock():
    extras = _write_extras(password_hash="", remember_user=True)
    assert password_is_configured(extras) is False
    assert startup_requires_authentication(extras) is False
    assert logout_requires_reauth(extras) is False


def test_restart_session_gate_matches_password_presence():
    hashed = hash_password(VALID_PASSWORD)
    with_pwd = _write_extras(password_hash=hashed, remember_user=True)
    assert startup_requires_authentication(with_pwd) is True

    no_pwd = _write_extras(password_hash="", remember_user=False)
    assert startup_requires_authentication(no_pwd) is False
    # Simulate cold start without password (same as main_window else-branch).
    session.login(no_pwd.get("administrator") or "Administrator", no_pwd.get("role") or "Administrator")
    assert session.authenticated is True
    session.logout()
    assert session.authenticated is False
    # Restart simulation: still no unlock gate without password.
    assert startup_requires_authentication(SettingsController().load_extras()) is False
    session.login("Administrator", "Administrator")
    assert session.authenticated is True


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
    infos = []

    monkeypatch.setattr(QApplication, "quit", lambda: quit_calls.append(1))
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *a, **k: infos.append(1) or QMessageBox.StandardButton.Ok,
    )

    host._logout()
    assert session.authenticated is False
    assert session.locked is True
    assert infos, "user must see an explicit logout confirmation"
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
