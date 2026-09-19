"""Login/unlock: mouse Prijava and ENTER must share one authentication path."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QMessageBox, QPushButton

from app.core.passwords import hash_password
from app.core.session import session
from app.windows.unlock_dialog import UnlockDialog

VALID_PASSWORD = "SecurePass1x"
INVALID_PASSWORD = "wrong-pass-99"


def _prepare_dialog(monkeypatch, password_hash: str | None = None) -> UnlockDialog:
    hashed = password_hash or hash_password(VALID_PASSWORD)
    dlg = UnlockDialog()
    dlg._hash = hashed
    # Avoid blocking modal warning boxes in headless tests.
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    session.authenticated = False
    session.locked = True
    session.last_activity = time.monotonic() - 10_000
    return dlg


def _run_with_trigger(dlg: UnlockDialog, trigger) -> int:
    QTimer.singleShot(30, trigger)
    QTimer.singleShot(2000, lambda: dlg.reject() if dlg.isVisible() else None)
    return dlg.exec()


def test_unlock_valid_password_mouse_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.password.setText(VALID_PASSWORD)
    result = _run_with_trigger(dlg, lambda: dlg.btn_save.click())
    assert result == QDialog.DialogCode.Accepted
    assert session.authenticated
    assert not session.locked


def test_unlock_valid_password_enter_same_as_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.password.setText(VALID_PASSWORD)

    def press_enter():
        dlg.password.setFocus()
        qt_app.processEvents()
        # After show/focus, Prijava must remain the default — not Izhod.
        assert dlg.btn_save.isDefault()
        assert not dlg.btn_cancel.isDefault()
        QTest.keyClick(dlg.password, Qt.Key.Key_Return)

    result = _run_with_trigger(dlg, press_enter)
    assert result == QDialog.DialogCode.Accepted
    assert session.authenticated
    assert not session.locked


def test_unlock_invalid_password_mouse_stays_open(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
    dlg.password.setText(INVALID_PASSWORD)
    warnings = []

    def _warn(*_a, **_k):
        warnings.append(1)
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
    assert not session.authenticated
    assert session.locked


def test_unlock_invalid_password_enter_same_as_click(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
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


def test_startup_login_enter_continues_mainwindow_path(qt_app, monkeypatch):
    """Mirrors main_window startup: Accepted unlock -> MainWindow may open."""
    dlg = _prepare_dialog(monkeypatch)
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
    # Same gate as app.windows.main_window startup after unlock.exec()
    assert result == QDialog.DialogCode.Accepted
    from app.windows.main_window import MainWindow

    window = MainWindow()
    assert window is not None
    window.close()


def test_unlock_dialog_enter_resets_idle_baseline(qt_app, monkeypatch):
    dlg = _prepare_dialog(monkeypatch)
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
