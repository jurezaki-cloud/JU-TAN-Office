"""Login/unlock: mouse Prijava and ENTER must share one authentication path."""

from __future__ import annotations

import json
import time

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton

from app.core.auth_gate import AUTH_ERROR_MESSAGE
from app.core.config_guard import stamp
from app.core.passwords import hash_password
from app.core.session import session
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import (
    SETTINGS_PATH,
    default_settings,
)
from app.windows.unlock_dialog import UnlockDialog

VALID_PASSWORD = "SecurePass1x"
INVALID_PASSWORD = "WrongPass99"
ADMIN_USER = "Administrator"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


@pytest.fixture(autouse=True)
def _cleanup_settings(qt_app):
    _wipe_users()
    yield
    _wipe_users()
    session.login("Administrator", "Administrator")
    session.locked = False
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()
    # Flush deferred Qt deletions from UnlockDialog.exec() paths.
    qt_app.processEvents()


def _write_credentials(*, remember_user: bool = True, role: str = "Administrator") -> str:
    hashed = hash_password(VALID_PASSWORD)
    data = default_settings()
    data.update(
        {
            "password_hash": hashed,
            "administrator": ADMIN_USER,
            "role": role,
            "remember_user": remember_user,
            "account_enabled": True,
            "setup_complete": True,
        }
    )
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(stamp(data), ensure_ascii=False), encoding="utf-8")
    return hashed


def _prepare_dialog(monkeypatch, *, remember_user: bool = True, role: str = "Administrator") -> UnlockDialog:
    _write_credentials(remember_user=remember_user, role=role)
    dlg = UnlockDialog()
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    session.authenticated = False
    session.locked = True
    session.last_activity = time.monotonic() - 10_000
    return dlg


def _run_with_trigger(dlg: UnlockDialog, trigger) -> int:
    QTimer.singleShot(30, trigger)
    QTimer.singleShot(2000, lambda: dlg.reject() if dlg.isVisible() else None)
    result = dlg.exec()
    dlg.close()
    dlg.deleteLater()
    return result


def test_unlock_valid_password_mouse_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(VALID_PASSWORD)
    result = _run_with_trigger(dlg, lambda: dlg.btn_save.click())
    assert result == QDialog.DialogCode.Accepted
    assert session.authenticated
    assert not session.locked


def test_unlock_valid_password_enter_same_as_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(VALID_PASSWORD)

    def press_enter():
        dlg.password.setFocus()
        qt_app.processEvents()
        assert dlg.btn_save.isDefault()
        assert not dlg.btn_cancel.isDefault()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)

    result = _run_with_trigger(dlg, press_enter)
    assert result == QDialog.DialogCode.Accepted
    assert session.authenticated
    assert not session.locked


def test_unlock_username_enter_focuses_password(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.clear()
    dlg.show()
    qt_app.processEvents()
    dlg.user.setFocus()
    qt_app.processEvents()
    QTest.keyClick(dlg.user, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert dlg.password.hasFocus()
    assert dlg.isVisible()
    assert not session.authenticated
    dlg.reject()


def test_unlock_invalid_password_mouse_stays_open(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(INVALID_PASSWORD)
    warnings = []

    def _warn(*_a, **kwargs):
        warnings.append(kwargs.get("text") or (_a[2] if len(_a) > 2 else ""))
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _warn)

    def click_and_close():
        dlg.btn_save.click()
        assert dlg.isVisible()
        assert not session.authenticated
        assert session.locked
        dlg.reject()

    result = _run_with_trigger(dlg, click_and_close)
    assert result == QDialog.DialogCode.Rejected
    assert warnings
    assert AUTH_ERROR_MESSAGE in str(warnings[0])
    assert not session.authenticated
    assert session.locked


def test_unlock_invalid_password_enter_same_as_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(INVALID_PASSWORD)
    warnings = []

    def _warn(*_a, **_k):
        warnings.append(1)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _warn)

    def enter_and_close():
        dlg.password.setFocus()
        qt_app.processEvents()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)
        qt_app.processEvents()
        assert dlg.isVisible()
        assert not session.authenticated
        assert session.locked
        dlg.reject()

    result = _run_with_trigger(dlg, enter_and_close)
    assert result == QDialog.DialogCode.Rejected
    assert warnings
    assert not session.authenticated
    assert session.locked


def test_unlock_wrong_username_stays_open(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText("nobody")
    dlg.password.setText(VALID_PASSWORD)
    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *a, **k: warnings.append(1) or QMessageBox.StandardButton.Ok,
    )

    def click_and_close():
        dlg.btn_save.click()
        assert dlg.isVisible()
        dlg.reject()

    result = _run_with_trigger(dlg, click_and_close)
    assert result == QDialog.DialogCode.Rejected
    assert warnings
    assert not session.authenticated


def test_startup_login_enter_continues_mainwindow_path(qt_app, monkeypatch):
    """Mirrors main_window startup: Accepted unlock -> MainWindow may open."""
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(VALID_PASSWORD)

    def press_enter():
        dlg.show()
        qt_app.processEvents()
        dlg.password.setFocus()
        qt_app.processEvents()
        for pb in dlg.findChildren(QPushButton):
            if pb.text() == "Izhod":
                assert not pb.isDefault(), "ENTER must not activate Izhod"
            if pb.text() == "Prijava":
                assert pb.isDefault()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)

    result = _run_with_trigger(dlg, press_enter)
    assert result == QDialog.DialogCode.Accepted
    assert session.authenticated
    from app.windows.main_window import MainWindow

    window = MainWindow()
    assert window is not None
    window.close()


def test_unlock_dialog_enter_resets_idle_baseline(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(VALID_PASSWORD)
    before = session.last_activity

    def press_enter():
        dlg.password.setFocus()
        qt_app.processEvents()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)

    result = _run_with_trigger(dlg, press_enter)
    assert result == QDialog.DialogCode.Accepted
    assert not session.locked
    assert session.authenticated
    assert session.last_activity >= before
    assert not session.idle_too_long()


def test_unlock_dialog_invalid_enter_remains_locked(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(INVALID_PASSWORD)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)

    def enter_and_close():
        dlg.password.setFocus()
        qt_app.processEvents()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)
        qt_app.processEvents()
        assert dlg.isVisible()
        dlg.reject()

    result = _run_with_trigger(dlg, enter_and_close)
    assert result != QDialog.DialogCode.Accepted
    assert session.locked
    assert not session.authenticated


def test_password_field_starts_empty(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch, remember_user=True)
    assert dlg.user.text() == ADMIN_USER
    assert dlg.password.text() == ""
    dlg.reject()


def test_remember_username_off_starts_empty(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch, remember_user=False)
    assert dlg.user.text() == ""
    assert dlg.password.text() == ""
    dlg.reject()


def test_login_restores_role_permissions(qt_app, monkeypatch):
    from app.core.permissions import can, current_role

    dlg = _prepare_dialog(monkeypatch, role="Sales")
    dlg.user.setText(ADMIN_USER)
    dlg.password.setText(VALID_PASSWORD)
    result = _run_with_trigger(dlg, lambda: dlg.btn_save.click())
    assert result == QDialog.DialogCode.Accepted
    assert current_role() == "Sales"
    assert can("users") is False
    assert can("write") is True


def test_close_login_rejects(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    result = _run_with_trigger(dlg, lambda: dlg.reject())
    assert result == QDialog.DialogCode.Rejected
    assert not session.authenticated


def test_enterprise_dialog_enter_activates_save_not_cancel(qt_app):
    from PySide6.QtWidgets import QLineEdit
    from app.core.ui.enterprise_dialog import EnterpriseDialog

    dialog = EnterpriseDialog(title="T", save_text="Prijava", cancel_text="Izhod", size="SMALL")
    field = QLineEdit()
    dialog.body.addWidget(field)
    hits = []
    dialog.bind_save(lambda: hits.append("save") or dialog.done(QDialog.DialogCode.Accepted))

    def press_enter():
        dialog.show()
        qt_app.processEvents()
        field.setFocus()
        qt_app.processEvents()
        assert dialog.btn_save.isDefault()
        assert not dialog.btn_cancel.isDefault()
        QTest.keyClick(field, Qt.Key.Key_Return)

    QTimer.singleShot(30, press_enter)
    QTimer.singleShot(2000, lambda: dialog.reject() if dialog.isVisible() else None)
    result = dialog.exec()
    assert result == QDialog.DialogCode.Accepted
    assert hits == ["save"]
