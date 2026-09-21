"""Namestitev, verzije, prvi zagon, nadgradnja."""

from app.core.constants import APP_CHANNEL, APP_VERSION, SCHEMA_VERSION
from app.core.setup_state import mark_setup_complete, needs_first_run
from app.core.update import check_for_update, is_newer, parse_version
from app.database.company_repository import company_repository


def test_versioning_major_minor_build():
    assert APP_VERSION == "1.0.0"
    assert APP_CHANNEL == "GOLD"
    assert parse_version("1.0.1") == (1, 0, 1)
    assert parse_version("1.1.0") > parse_version("1.0.2")
    assert is_newer("1.0.1", "1.0.0")
    assert not is_newer("1.0.0", "1.0.0")
    assert not is_newer("1.0.0", "1.0.1")


def test_schema_version_constant():
    assert SCHEMA_VERSION == 2


def test_release_meta_matches_constants():
    from app.core import release_meta

    assert release_meta.APP_VERSION == APP_VERSION
    assert release_meta.APP_CHANNEL == APP_CHANNEL
    assert release_meta.SCHEMA_VERSION == SCHEMA_VERSION


def test_first_run_then_complete():
    row = company_repository.get_company()
    if row and (row[1] or "").strip():
        company_repository.save(
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
            "RAC", "PON", 1, 1, 22, "",
        )
    assert needs_first_run()
    mark_setup_complete(administrator="QA Admin", currency="EUR")
    assert not needs_first_run()


def test_check_for_update_local_json(tmp_path):
    payload = tmp_path / "latest.json"
    payload.write_text('{"version": "9.9.9", "notes": "test"}', encoding="utf-8")
    found = check_for_update(payload)
    assert found is not None
    assert found["version"] == "9.9.9"
    none = tmp_path / "same.json"
    none.write_text('{"version": "1.0.0"}', encoding="utf-8")
    assert check_for_update(none) is None


def test_apply_schema_upgrade_writes_version(tmp_path):
    from app.core import update as update_mod
    from app.core.update import apply_schema_upgrade

    mark = update_mod.VERSION_MARK
    mark.write_text("0.9.0", encoding="utf-8")
    apply_schema_upgrade()
    assert mark.read_text(encoding="utf-8").strip() == APP_VERSION


def test_upgrade_backup_and_rollback(tmp_path):
    from app.core.update import backup_for_upgrade, rollback
    from app.database.customer_repository import customer_repository

    customer_repository.add("Deploy d.o.o.", "QA", "", "", "Koper", "SI", "", "", "")
    backup = backup_for_upgrade()
    assert backup.exists()
    rollback(backup)
    found = customer_repository.search("Deploy d.o.o.")
    assert found
