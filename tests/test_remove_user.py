"""Odstrani uporabnika — physical delete vs archive, service protections."""

from __future__ import annotations

import json

import pytest

from app.core.auth_gate import authenticate_credentials
from app.core.config_guard import stamp
from app.core.fresh_reset import FRESH_CONFIRM_TEXT, FreshResetService
from app.core.permissions import AUDIT_FILE, audit, can
from app.core.session import session
from app.core.user_service import (
    LastAdminError,
    SelfRemovalError,
    apply_session_for_user,
    assess_user_removal,
    create_first_administrator,
    create_user,
    remove_user,
    user_has_historical_references,
)
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import SETTINGS_PATH, default_settings

VALID_PASSWORD = "SecurePass1x"
VALID_PASSWORD_2 = "SecurePass2y"
VALID_PASSWORD_3 = "SecurePass3z"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")
        try:
            conn.execute("DELETE FROM audit_log")
        except Exception:
            pass
    try:
        if AUDIT_FILE.exists():
            AUDIT_FILE.unlink()
    except OSError:
        pass


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


def _admin_with_sales() -> tuple[dict, dict]:
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    sales = create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
    return admin, sales


def test_admin_can_remove_ordinary_user():
    admin, tanja = _admin_with_sales()
    result = remove_user(tanja["id"])
    assert result.mode == "physical"
    assert user_repository.get_by_id(tanja["id"]) is None
    # Admin session still consistent
    assert session.user_id == admin["id"]
    assert can("users") is True
    assert user_repository.get_by_id(admin["id"]) is not None


def test_non_admin_cannot_remove_user():
    admin, tanja = _admin_with_sales()
    other = create_user(username="Marko", password=VALID_PASSWORD_3, role="Sales")
    apply_session_for_user(tanja)
    assert can("users") is False
    with pytest.raises(PermissionError):
        remove_user(other["id"])
    assert user_repository.get_by_id(other["id"]) is not None


def test_removed_user_cannot_login():
    _, tanja = _admin_with_sales()
    remove_user(tanja["id"])
    ok, _ = authenticate_credentials("Tanja", VALID_PASSWORD_2, {})
    assert not ok


def test_user_with_history_is_archived_not_erased():
    admin, tanja = _admin_with_sales()
    # Create actor history for Tanja
    apply_session_for_user(tanja)
    audit("write", "invoice:demo")
    apply_session_for_user(admin)

    assert user_has_historical_references(tanja["id"], "Tanja") is True
    assessment = assess_user_removal(tanja["id"])
    assert assessment.mode == "archive"

    result = remove_user(tanja["id"])
    assert result.mode == "archive"
    row = user_repository.get_by_id(tanja["id"])
    assert row is not None
    assert row["username"] == "Tanja"
    assert row["is_active"] is False
    assert row["id"] == tanja["id"]

    # History preserved
    conn = db.connect()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE username=? OR detail LIKE ?",
            ("Tanja", f"%[uid={tanja['id']}]%"),
        ).fetchone()[0]
    finally:
        conn.close()
    assert count >= 1

    # Old password cannot restore access
    ok, _ = authenticate_credentials("Tanja", VALID_PASSWORD_2, {})
    assert not ok


def test_unreferenced_user_may_be_physically_deleted():
    _, tanja = _admin_with_sales()
    # Never logged in as Tanja → no actor history
    assert user_has_historical_references(tanja["id"], "Tanja") is False
    result = remove_user(tanja["id"])
    assert result.mode == "physical"
    assert user_repository.get_by_id(tanja["id"]) is None


def test_final_active_administrator_cannot_be_removed():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    with pytest.raises(LastAdminError):
        remove_user(admin["id"])
    assert user_repository.get_by_id(admin["id"]) is not None
    assert user_repository.count_active_admins() == 1


def test_last_admin_protection_at_service_layer():
    """Protection is enforced by remove_user(), not only UI."""
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
    # Still only one admin — cannot remove Jure via service
    with pytest.raises(LastAdminError):
        remove_user(admin["id"])


def test_current_session_remains_consistent_and_blocks_self_removal():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    second = create_user(
        username="Boss2",
        password=VALID_PASSWORD_2,
        role="Administrator",
        permissions=None,
    )
    # Second admin exists so last-admin does not apply; self-removal still blocked.
    with pytest.raises(SelfRemovalError):
        remove_user(admin["id"])
    assert session.authenticated is True
    assert session.user_id == admin["id"]
    assert can("users") is True
    assert user_repository.get_by_id(admin["id"])["is_active"] is True
    # Other admin unaffected and removable by current session
    remove_user(second["id"])
    assert user_repository.get_by_id(admin["id"]) is not None


def test_other_users_unaffected_by_removal():
    admin, tanja = _admin_with_sales()
    marko = create_user(username="Marko", password=VALID_PASSWORD_3, role="Read Only")
    remove_user(tanja["id"])
    assert user_repository.get_by_id(admin["id"]) is not None
    assert user_repository.get_by_id(marko["id"]) is not None
    assert user_repository.get_by_id(marko["id"])["is_active"] is True
    ok, _ = authenticate_credentials("Marko", VALID_PASSWORD_3, {})
    assert ok


def test_fresh_behavior_unaffected(tmp_path):
    """Normal user removal must not change Fresh semantics."""
    data = tmp_path / "data"
    backup = tmp_path / "backup"
    data.mkdir()
    backup.mkdir()
    db_path = data / "ju_tan.db"

    from app.database import database as database_mod

    previous = database_mod.db.database
    database_mod.db.dispose()
    database_mod.db.database = db_path
    try:
        database_mod.db.initialize()
        _wipe_users()
        admin = create_first_administrator("Jure", VALID_PASSWORD)
        apply_session_for_user(admin)
        create_user(username="Tanja", password=VALID_PASSWORD_2, role="Sales")
        remove_user(user_repository.get_by_username("Tanja")["id"])

        settings = {
            **default_settings(),
            "setup_complete": True,
            "administrator": "Jure",
            "remember_user": True,
            "password_hash": "",
            "legacy_auth_migrated": True,
        }
        (data / "settings.json").write_text(
            json.dumps(stamp(settings), ensure_ascii=False), encoding="utf-8"
        )

        service = FreshResetService(data_dir=data, backup_dir=backup)
        service.database_path = db_path
        apply_session_for_user(admin)
        backup_path = service.execute(password=VALID_PASSWORD, confirm_text=FRESH_CONFIRM_TEXT)
        assert backup_path.is_dir()
        assert user_repository.count_users() == 0
        assert session.authenticated is False
    finally:
        database_mod.db.dispose()
        database_mod.db.database = previous
        database_mod.db.initialize()
        _wipe_users()
        session.login("Administrator", "Administrator")
