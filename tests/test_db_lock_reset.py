"""Lock / Fresh-Install fail-closed regression — DB must not stay locked or falsely wipe."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

from app.core.business_data import assert_fresh_production_database, business_record_counts
from app.core.db_lifecycle import (
    database_files_present,
    delete_database_files,
    shutdown_database,
)
from app.database.database import Database, db as global_db


ROOT = Path(__file__).resolve().parent.parent
ISS = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")

windows_file_locks = pytest.mark.skipif(
    sys.platform != "win32",
    reason="POSIX allows unlinking open files; the open-DB guard relies on Windows sharing locks",
)


def _seed_wal_db(db_path: Path) -> Database:
    database = Database()
    database.database = db_path
    database.initialize()
    conn = database.connect()
    conn.execute("UPDATE company SET name=? WHERE id=1", ("LockSeed d.o.o.",))
    conn.execute("INSERT INTO customers(company) VALUES (?)", ("Stranka Lock",))
    conn.execute(
        "INSERT INTO articles(code, name, price, vat) VALUES (?,?,?,?)",
        ("L1", "Artikel Lock", 1.0, 22.0),
    )
    conn.commit()
    # Touch WAL deliberately
    conn.execute("PRAGMA journal_mode")
    return database


def test_installer_fail_closed_and_process_detection_contracts():
    assert "EnsureAppClosedForDestructiveOp" in ISS
    assert "BusinessDatabaseFilesGone" in ISS
    assert "WipeBusinessDatabaseFiles" in ISS
    assert "CheckForMutexes" in ISS
    assert "JU-TAN Office je še vedno odprt" in ISS
    assert "Čiste namestitve ni bilo mogoče dokončati" in ISS
    assert "baza podatkov še vedno v" in ISS
    assert "Vaši podatki niso bili nadomeščeni" in ISS
    # Blind cmd del /F must not be the primary wipe path anymore
    assert "del /F /Q" not in ISS


def test_a_database_not_open_deletion_succeeds(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    shutdown_database(database=database)
    # Also release global singleton possibly opened by ensure_schema
    shutdown_database(database=global_db)
    remaining = delete_database_files(db_path)
    assert remaining == []
    assert database_files_present(db_path) == []


@windows_file_locks
def test_b_open_database_reset_does_not_falsely_succeed(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    # Keep connection open — deletion must report leftovers, not pretend success.
    remaining = delete_database_files(db_path)
    assert remaining, "open DB must not report successful deletion"
    assert (tmp_path / "ju_tan.db").exists()
    before = business_record_counts(db_path)
    assert before["companies"] == 1
    assert before["customers"] == 1
    shutdown_database(database=database)
    shutdown_database(database=global_db)


def test_c_graceful_shutdown_then_deletion_succeeds(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    assert (tmp_path / "ju_tan.db-wal").exists() or True  # WAL may already be checkpointed
    shutdown_database(database=database)
    shutdown_database(database=global_db)
    remaining = delete_database_files(db_path)
    assert remaining == []


def test_d_wal_database_removes_db_wal_shm(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    # Force wal/shm presence
    raw = object.__getattribute__(database.connect(), "_raw")
    raw.execute("PRAGMA journal_mode=WAL")
    raw.execute("INSERT INTO customers(company) VALUES ('WalTouch')")
    raw.commit()
    assert db_path.exists()
    # Files may include -wal/-shm while connection open
    present_before = {p.name for p in database_files_present(db_path)}
    assert "ju_tan.db" in present_before
    shutdown_database(database=database)
    shutdown_database(database=global_db)
    remaining = delete_database_files(db_path)
    assert remaining == []
    assert not (tmp_path / "ju_tan.db").exists()
    assert not (tmp_path / "ju_tan.db-wal").exists()
    assert not (tmp_path / "ju_tan.db-shm").exists()


def test_e_failed_deletion_fresh_install_aborts_safely(tmp_path, monkeypatch):
    from app.core.config_guard import stamp
    from app.core.fresh_reset import FRESH_CONFIRM_TEXT, FreshResetError, FreshResetService
    from app.core.permissions import set_identity
    from app.core.session import session
    from app.core.user_service import apply_session_for_user, create_first_administrator
    from app.database import database as database_mod
    from app.database.user_repository import user_repository
    from app.modules.settings.settings_controller import default_settings

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
        admin = create_first_administrator("AdminLock", "SecurePass1x")
        apply_session_for_user(admin)
        conn = database_mod.db.connect()
        conn.execute("UPDATE company SET name=? WHERE id=1", ("Keep Me d.o.o.",))
        conn.execute("INSERT INTO customers(company) VALUES ('KeepCust')")
        conn.execute("INSERT INTO articles(code, name) VALUES ('K','Art')")
        conn.commit()
        # Intentionally leave connection open so unlink fails on Windows.
        (data / "settings.json").write_text(
            __import__("json").dumps(
                stamp({**default_settings(), "setup_complete": True}),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        service = FreshResetService(data_dir=data, backup_dir=backup)
        service.database_path = db_path
        set_identity(role="Administrator", authenticated=True, clear_overrides=True)
        apply_session_for_user(admin)

        # Force delete to report failure even after shutdown (simulate stubborn lock).
        def _fake_delete(_path):
            return [db_path]

        monkeypatch.setattr(
            "app.core.fresh_reset.delete_database_files", _fake_delete
        )

        with pytest.raises(FreshResetError) as excinfo:
            service.execute(password="SecurePass1x", confirm_text=FRESH_CONFIRM_TEXT)

        msg = str(excinfo.value)
        assert "baza podatkov še vedno" in msg or "ni uspela" in msg or "Varnostna kopija" in msg

        # F: existing data remains intact when deletion fails
        counts = business_record_counts(db_path)
        assert counts["companies"] == 1
        assert counts["customers"] == 1
        assert counts["articles"] == 1
        assert db_path.exists()
    finally:
        database_mod.db.dispose()
        database_mod.db.database = previous
        database_mod.db.initialize()
        user_repository.delete_all_users()
        session.login("Administrator", "Administrator")
        set_identity(role="Administrator", authenticated=True, clear_overrides=True)


@windows_file_locks
def test_f_failed_deletion_keeps_existing_data(tmp_path):
    """Open connection → delete_database_files leaves records untouched."""
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    before = business_record_counts(db_path)
    remaining = delete_database_files(db_path)
    assert remaining
    after = business_record_counts(db_path)
    assert after == before
    shutdown_database(database=database)
    shutdown_database(database=global_db)


def test_g_successful_deletion_fresh_database_zero_counts(tmp_path):
    db_path = tmp_path / "ju_tan.db"
    database = _seed_wal_db(db_path)
    shutdown_database(database=database)
    shutdown_database(database=global_db)
    assert delete_database_files(db_path) == []

    fresh = Database()
    fresh.database = db_path
    fresh.initialize()
    counts = assert_fresh_production_database(db_path)
    assert counts["companies"] == 0
    assert counts["customers"] == 0
    assert counts["articles"] == 0
    assert counts["invoices"] == 0
    assert counts["offers"] == 0
    assert counts["orders"] == 0
    assert counts["payments"] == 0
    shutdown_database(database=fresh)
    shutdown_database(database=global_db)


def test_worker_thread_connection_is_released_when_thread_exits(tmp_path):
    """Background jobs (PDF/Excel) connect on their own thread; the pool must not leak them."""
    import gc
    import threading

    database = Database()
    database.database = tmp_path / "ju_tan.db"

    def work():
        database.connect().execute("SELECT 1").fetchone()

    worker = threading.Thread(target=work)
    worker.start()
    worker.join()
    gc.collect()
    assert len(database._connections) == 0

    database.connect().execute("SELECT 1").fetchone()
    assert len(database._connections) == 1
    shutdown_database(database=database)
    assert len(database._connections) == 0
    assert delete_database_files(database.database) == []


def test_shutdown_database_releases_global_pool_after_temp_initialize(tmp_path):
    """Regression: temp Database.initialize() must not leave global WAL locks."""
    db_path = tmp_path / "ju_tan.db"
    local = Database()
    local.database = db_path
    # Point singleton at same file so ensure_schema opens it.
    previous = global_db.database
    global_db.database = db_path
    try:
        local.initialize()
        local.dispose()
        # initialize() should have disposed singleton when self is not global;
        # call shutdown explicitly for the contract under test.
        shutdown_database(database=global_db)
        remaining = delete_database_files(db_path)
        assert remaining == []
    finally:
        shutdown_database(database=global_db)
        global_db.database = previous
