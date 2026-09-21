"""UI tests for the premium First Launch Wizard (no business-logic changes)."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from app.core.setup_state import mark_setup_complete, needs_first_run
from app.core.user_service import users_exist
from app.database.company_repository import company_repository
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import SETTINGS_PATH, SettingsController
from app.windows.first_run_wizard import (
    STEP_COMPANY,
    STEP_COMPLETE,
    STEP_LICENSE,
    STEP_SECURITY,
    STEP_USER,
    STEP_WELCOME,
    FirstRunWizard,
)

VALID_PASSWORD = "SecurePass1x"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    from app.database.database import db

    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


@pytest.fixture(autouse=True)
def _cleanup():
    _wipe_users()
    yield
    _wipe_users()
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()


def _clear_company() -> None:
    company_repository.save(
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "RAC",
        "PON",
        1,
        1,
        22,
        "",
    )


def test_first_launch_path_shows_wizard_steps(qt_app):
    _clear_company()
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()
    assert needs_first_run() is True

    wizard = FirstRunWizard()
    assert wizard.objectName() == "FirstRunWizard"
    assert wizard.stack.count() == 6
    assert wizard._step == STEP_WELCOME
    assert wizard.btn_next.text() == "Začni"
    assert not wizard.btn_back.isEnabled()

    wizard._next()
    assert wizard._step == STEP_COMPANY
    wizard.company.setText("Demo d.o.o.")
    wizard._next()
    assert wizard._step == STEP_USER
    wizard.close()


def test_existing_user_path_skips_first_run(qt_app):
    mark_setup_complete(administrator="Existing", currency="EUR")
    company_repository.save(
        "Existing Co",
        "Existing Co",
        "",
        "",
        "",
        "Slovenija",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "RAC",
        "PON",
        1,
        1,
        22,
        "",
        1,
    )
    assert needs_first_run() is False


def test_cancel_closes_wizard_without_setup(qt_app, monkeypatch):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    wizard = FirstRunWizard()
    wizard.company.setText("Temp d.o.o.")
    wizard.reject()
    assert wizard.result() == QDialog.DialogCode.Rejected
    extras = SettingsController().load_extras()
    assert not extras.get("setup_complete")
    assert users_exist() is False
    wizard.close()


def test_security_and_license_steps_are_guidance_only(qt_app, monkeypatch):
    warnings = []

    def _warn(parent, title, text, *a, **k):
        warnings.append(text)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _warn)
    wizard = FirstRunWizard()
    wizard._show_step(STEP_SECURITY)
    wizard._next()
    assert any("kontrolnega seznama" in w.lower() for w in warnings)
    assert wizard._step == STEP_SECURITY

    for box in wizard._security_checks:
        box.setChecked(True)
    wizard._next()
    assert wizard._step == STEP_LICENSE
    # License step must not call activation APIs — navigating is enough.
    wizard._next()
    assert wizard._step == STEP_COMPLETE
    assert "Nastavitvah" in wizard.complete_summary.text()
    wizard.close()


def test_finish_from_completion_preserves_business_path(qt_app, monkeypatch):
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
    wizard._show_step(STEP_COMPLETE)
    wizard._next()

    extras = SettingsController().load_extras()
    assert extras["setup_complete"] is True
    assert extras["administrator"] == "boss"
    assert saved.get("company") == "ACME d.o.o."
    assert users_exist() is True
    wizard.close()


def test_direct_finish_api_compatible_with_legacy_tests(qt_app, monkeypatch):
    """Existing auth tests call fields + _finish() without stepping the UI."""
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(
        "app.windows.first_run_wizard.company_repository.save",
        lambda *a, **k: None,
    )
    wizard = FirstRunWizard()
    assert wizard.admin.text() == ""
    wizard.company.setText("Legacy API Co")
    wizard.admin.setText("admin1")
    wizard.password.setText(VALID_PASSWORD)
    wizard.password2.setText(VALID_PASSWORD)
    wizard._finish()
    assert SettingsController().load_extras().get("setup_complete") is True
    wizard.close()
