"""Fresh install / uninstall architecture — production safety contracts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.core.business_data import (
    assert_fresh_production_database,
    business_record_counts,
    is_business_empty,
)
from app.core.data_locations import (
    business_data_markers,
    localappdata_license_root,
    owned_locations,
    previous_business_data_exists,
    programdata_root,
)
from app.core.fresh_reset import FRESH_CONFIRM_TEXT, FreshResetService
from app.database.database import Database
from app.modules.settings.settings_controller import default_settings


ROOT = Path(__file__).resolve().parent.parent
ISS = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
SPEC = (ROOT / "packaging" / "ju-tan-office.spec").read_text(encoding="utf-8")


def test_installer_does_not_ship_database_files():
    assert "ju_tan.db" not in SPEC
    assert "ju_tan_demo.db" not in SPEC
    assert "warehouse_demo.json" not in SPEC
    assert "*.db" not in ISS
    assert "ju_tan_demo" not in ISS


def test_installer_fresh_and_uninstall_contracts():
    assert "Nadgradi / ponovno namesti in ohrani podatke" in ISS
    assert "Nova čista namestitev" in ISS
    assert "Odstrani program" in ISS
    assert "Popolnoma odstrani JU-TAN Office in vse podatke" in ISS
    assert "Izbriši tudi lokalne varnostne kopije" in ISS
    assert "Pred izbrisom ustvari varnostno kopijo" in ISS
    assert "Ustvari varnostno kopijo in nadaljuj" in ISS or "Da = Ustvari varnostno kopijo" in ISS
    assert "POZOR" in ISS
    assert "uninsneveruninstall" in ISS
    assert "WipeBusinessDataKeepBackups" in ISS
    assert "FreshInstallChosen" in ISS
    assert "WizardSilent" in ISS
    assert "UninstallSilent" in ISS
    assert "license_preserved" in ISS
    assert r"{localappdata}\JU-TAN\Office" in ISS or "LicenseStateDir" in ISS
    assert "pre-upgrade.db-wal" in ISS
    assert "DATA_LOCATIONS.md" in ISS
    # Silent paths must not auto-wipe
    assert "FreshInstallChosen := False" in ISS
    # Fail-closed wipe + process detection
    assert "EnsureAppClosedForDestructiveOp" in ISS
    assert "BusinessDatabaseFilesGone" in ISS
    assert "Čiste namestitve ni bilo mogoče dokončati" in ISS
    assert "{param:FRESH|0}" in ISS or "param:FRESH" in ISS
    # Official Slovenian Inno Setup language pack (not hand-hacked button strings)
    assert "[Languages]" in ISS
    assert r'compiler:Languages\Slovenian.isl' in ISS
    assert "č" in ISS and "š" in ISS and "ž" in ISS


def test_installer_backups_fail_closed_and_stay_consistent():
    # Fresh-install backup: any copy failure (files or documents) aborts before the wipe.
    assert "CopyRequired(DataDir + '\\settings.json'" in ISS
    assert "CopyRequired(DataDir + '\\ju_tan.db-wal'" in ISS
    assert "(ExitCode > 1)" in ISS
    # Upgrade backup: stale sidecars from an older upgrade must never pair with a newer DB.
    body = ISS.split("procedure BackupDatabaseBeforeUpgrade", 1)[1].split("end;", 1)[0]
    assert body.index("DeleteFile(BackupDir + '\\pre-upgrade.db-wal')") < body.index(
        "CopyFile(DataDir + '\\ju_tan.db'"
    )
    # The user's visible choice decides; the EULA is never pre-accepted for them.
    assert "LicenseAcceptedRadio" not in ISS
    assert "ForceFresh" not in ISS


def test_data_locations_inventory_covers_programdata_and_license():
    locs = {item.key: item for item in owned_locations(runtime_root=programdata_root())}
    assert "data" in locs
    assert "backup" in locs
    assert "license_activation" in locs
    assert locs["backup"].removable_on_complete_uninstall is False
    assert locs["license_activation"].removable_on_fresh_install is False
    assert locs["license_activation"].removable_on_complete_uninstall is False
    assert "JU-TAN" in str(localappdata_license_root())


def test_previous_business_data_detection(tmp_path):
    data = tmp_path / "Data"
    data.mkdir()
    assert previous_business_data_exists(data) is False
    (data / "settings.json").write_text("{}", encoding="utf-8")
    assert previous_business_data_exists(data) is True
    assert any(p.name == "settings.json" for p in business_data_markers(data))


def test_fresh_database_initialize_has_zero_business_records(tmp_path, monkeypatch):
    db_path = tmp_path / "ju_tan.db"
    database = Database()
    database.database = db_path
    database.initialize()
    counts = assert_fresh_production_database(db_path)
    assert counts["companies"] == 0
    assert counts["customers"] == 0
    assert counts["articles"] == 0
    assert counts["invoices"] == 0
    assert counts["offers"] == 0
    assert counts["orders"] == 0
    assert counts["payments"] == 0
    assert counts["suppliers"] == 0
    assert counts["purchases"] == 0
    assert is_business_empty(counts)

    conn = sqlite3.connect(db_path)
    try:
        # System scaffold row may exist with blank name — not a business company.
        row = conn.execute("SELECT name FROM company WHERE id=1").fetchone()
        assert row is not None
        assert not (row[0] or "").strip()
        assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0
    finally:
        conn.close()
    database.dispose()


def test_fresh_database_contains_no_demo_names(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = Database()
    database.database = db_path
    database.initialize()
    assert_fresh_production_database(db_path)
    database.dispose()


def test_upgrade_preserves_seeded_business_data(tmp_path):
    """Simulate upgrade: re-initialize schema on existing DB must keep rows."""
    db_path = tmp_path / "ju_tan.db"
    database = Database()
    database.database = db_path
    database.initialize()
    conn = database.connect()
    conn.execute("UPDATE company SET name=? WHERE id=1", ("Obstoječe d.o.o.",))
    conn.execute("INSERT INTO customers(company) VALUES (?)", ("Stranka A",))
    conn.execute(
        "INSERT INTO articles(code, name, price, vat) VALUES (?,?,?,?)",
        ("A1", "Artikel 1", 10.0, 22.0),
    )
    conn.commit()
    conn.close()

    before = business_record_counts(db_path)
    assert before["companies"] == 1
    assert before["customers"] == 1
    assert before["articles"] == 1

    # Re-run initialize as an upgrade/reinstall would (CREATE IF NOT EXISTS only).
    database.initialize()
    after = business_record_counts(db_path)
    assert after == before
    database.dispose()


def test_fresh_reset_empties_business_and_keeps_backup(tmp_path):
    from app.core.config_guard import stamp
    from app.core.permissions import set_identity
    from app.core.session import session
    from app.core.user_service import apply_session_for_user, create_first_administrator
    from app.database import database as database_mod
    from app.database.user_repository import user_repository

    data = tmp_path / "data"
    backup = tmp_path / "backup"
    data.mkdir()
    backup.mkdir()
    db_path = data / "ju_tan.db"

    previous = database_mod.db.database
    database_mod.db.dispose()
    database_mod.db.database = db_path
    try:
        database_mod.db.initialize()
        user_repository.delete_all_users()
        admin = create_first_administrator("AdminFresh", "SecurePass1x")
        apply_session_for_user(admin)
        conn = database_mod.db.connect()
        conn.execute("UPDATE company SET name=? WHERE id=1", ("Demo Co",))
        conn.execute("INSERT INTO customers(company) VALUES ('Cust')")
        conn.execute(
            "INSERT INTO articles(code, name) VALUES ('X','Art')"
        )
        conn.commit()
        conn.close()
        (data / "settings.json").write_text(
            json.dumps(stamp({**default_settings(), "setup_complete": True}), ensure_ascii=False),
            encoding="utf-8",
        )

        service = FreshResetService(data_dir=data, backup_dir=backup)
        service.database_path = db_path
        set_identity(role="Administrator", authenticated=True, clear_overrides=True)
        apply_session_for_user(admin)
        backup_path = service.execute(password="SecurePass1x", confirm_text=FRESH_CONFIRM_TEXT)

        assert backup_path.is_dir()
        assert (backup_path / "ju_tan.db").is_file()
        counts = assert_fresh_production_database(db_path)
        assert counts["companies"] == 0
        assert counts["customers"] == 0
        assert counts["articles"] == 0
    finally:
        database_mod.db.dispose()
        database_mod.db.database = previous
        database_mod.db.initialize()
        user_repository.delete_all_users()
        session.login("Administrator", "Administrator")
        set_identity(role="Administrator", authenticated=True, clear_overrides=True)


def test_docs_data_locations_exist():
    assert (ROOT / "docs" / "DATA_LOCATIONS.md").is_file()
    text = (ROOT / "docs" / "DATA_LOCATIONS.md").read_text(encoding="utf-8")
    assert "ProgramData" in text
    assert "LocalAppData" in text
    assert "Odstrani program" in text or "standardn" in text.casefold()


def test_migrations_idempotent_on_fresh_db(tmp_path):
    from app.core.constants import SCHEMA_VERSION
    from app.database.migrations import apply_pending_migrations

    db_path = tmp_path / "ju_tan.db"
    database = Database()
    database.database = db_path
    database.initialize()
    with database.transaction() as conn:
        apply_pending_migrations(0, SCHEMA_VERSION, conn)
        apply_pending_migrations(SCHEMA_VERSION, SCHEMA_VERSION, conn)
    assert_fresh_production_database(db_path)
    database.dispose()
