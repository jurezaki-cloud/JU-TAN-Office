"""P0 regresija za 1.0.8: geslo, RBAC, obnova baze, zaloga."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.auth_gate import authenticate_credentials
from app.core.passwords import verify_password
from app.core.permissions import set_identity
from app.core.session import session
from app.core.user_service import (
    apply_session_for_user,
    create_first_administrator,
    create_user,
)
from app.database.database import db
from app.database.invoice_repository import invoice_repository
from app.database.payment_repository import payment_repository
from app.database.reminder_repository import reminder_repository
from app.database.user_repository import user_repository
from app.database.customer_repository import customer_repository
from app.database.article_repository import article_repository
from app.modules.crm.crm_controller import CrmController
from app.modules.crm.crm_repository import crm_repository
from app.modules.documents.documents_repository import documents_repository
from app.modules.documents.documents_service import DocumentsService
from app.modules.settings.settings_controller import SettingsController
from app.modules.warehouse.warehouse_service import WarehouseService, WarehouseStoreError

ADMIN_PASSWORD = "SecurePass1x"
SALES_PASSWORD = "SecurePass2y"
READER_PASSWORD = "SecurePass3z"
ACCOUNTING_PASSWORD = "SecurePass4w"
NEW_PASSWORD = "SecurePass9z"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


def _as_admin() -> None:
    set_identity(role="Administrator", authenticated=True, clear_overrides=True)
    session.login("Administrator", "Administrator")
    session.locked = False


@pytest.fixture(autouse=True)
def _clean_identity():
    _wipe_users()
    _as_admin()
    yield
    _wipe_users()
    _as_admin()


def test_password_change_uses_users_table_and_checks_old_password():
    admin = create_first_administrator("Jure", ADMIN_PASSWORD)
    sales = create_user(username="Tanja", password=SALES_PASSWORD, role="Sales")
    apply_session_for_user(sales)
    controller = SettingsController()
    before = user_repository.get_by_id(sales["id"])["password_hash"]

    with pytest.raises(PermissionError, match="Trenutno geslo"):
        controller.change_password("", NEW_PASSWORD)
    with pytest.raises(PermissionError, match="Trenutno geslo"):
        controller.change_password("WrongPass1x", NEW_PASSWORD)
    assert user_repository.get_by_id(sales["id"])["password_hash"] == before
    assert not verify_password(NEW_PASSWORD, before)

    controller.change_password(SALES_PASSWORD, NEW_PASSWORD)
    updated = user_repository.get_by_id(sales["id"])
    assert verify_password(NEW_PASSWORD, updated["password_hash"])
    assert not verify_password(SALES_PASSWORD, updated["password_hash"])
    ok, err = authenticate_credentials("Tanja", NEW_PASSWORD, {})
    assert ok and err is None
    ok, err = authenticate_credentials("Tanja", SALES_PASSWORD, {})
    assert not ok

    extras = controller.load_extras()
    assert extras.get("password_hash") in ("", None)
    assert verify_password(NEW_PASSWORD, extras.get("password_hash") or "") is False

    apply_session_for_user(admin)
    with pytest.raises(PermissionError):
        controller.change_password(NEW_PASSWORD, ADMIN_PASSWORD)
    assert verify_password(NEW_PASSWORD, user_repository.get_by_id(sales["id"])["password_hash"])


def test_legacy_password_change_never_skips_old_password():
    controller = SettingsController()
    from app.core.passwords import hash_password

    previous = controller.load_extras()
    try:
        extras = dict(previous)
        extras["password_hash"] = ""
        controller.save_extras(extras)
        with pytest.raises(PermissionError, match="Trenutno geslo"):
            controller.change_password("anything1A", NEW_PASSWORD)

        stored = hash_password(ADMIN_PASSWORD)
        extras = controller.load_extras()
        extras["password_hash"] = stored
        controller.save_extras(extras)
        with pytest.raises(PermissionError, match="Trenutno geslo"):
            controller.change_password("WrongPass1x", NEW_PASSWORD)
        assert controller.load_extras()["password_hash"] == stored
        controller.change_password(ADMIN_PASSWORD, NEW_PASSWORD)
        assert verify_password(NEW_PASSWORD, controller.load_extras()["password_hash"])
    finally:
        controller.save_extras(previous)


def test_readonly_cannot_modify_payments_crm_or_documents(tmp_path):
    _as_admin()
    controller = CrmController()
    deal_id = controller.create_lead({
        "company": "P0 CRM d.o.o.",
        "contact": "Ana",
        "title": "P0 lead",
        "stage": "Lead",
        "value": 10,
    })
    documents = DocumentsService(root=tmp_path / "docs")
    folder_id = documents.repository.add(name="P0 mapa", is_folder=True, owner="QA")
    file_id = documents.repository.add(
        name="p0.txt",
        parent_id=folder_id,
        is_folder=False,
        kind="txt",
        extension="txt",
        owner="QA",
    )

    set_identity(role="Read Only", authenticated=True, clear_overrides=True)
    with pytest.raises(PermissionError):
        payment_repository.add(1, "2026-10-21", 10, "Nakazilo")
    with pytest.raises(PermissionError):
        payment_repository.sync_invoice_status(1, 10)
    with pytest.raises(PermissionError):
        reminder_repository.add(1, 1, "a@example.com", "Opomin", 10)
    with pytest.raises(PermissionError):
        invoice_repository.mark_paid(1)
    with pytest.raises(PermissionError):
        controller.update_deal(deal_id, {"title": "Spremenjeno"})
    with pytest.raises(PermissionError):
        controller.add_note(None, deal_id, "skrita opomba", "RO")
    with pytest.raises(PermissionError):
        crm_repository.set_stage(deal_id, "Won")
    with pytest.raises(PermissionError):
        documents.rename(file_id, "drugo.txt")
    with pytest.raises(PermissionError):
        documents.move(file_id, None)
    with pytest.raises(PermissionError):
        documents.copy(file_id, None)
    with pytest.raises(PermissionError):
        documents.delete(file_id)
    with pytest.raises(PermissionError):
        documents.repository.add(name="nov.txt", is_folder=False, owner="RO")

    _as_admin()
    deal = crm_repository.get_deal(deal_id)
    assert deal[3] == "P0 lead"
    assert documents.repository.get(file_id)[2] == "p0.txt"
    with pytest.raises(ValueError):
        payment_repository.add(999999, "2026-10-21", 10, "Nakazilo")


def test_restore_rechecks_admin_identity_against_users_table():
    admin = create_first_administrator("Jure", ADMIN_PASSWORD)
    reader = create_user(username="Bralec", password=READER_PASSWORD, role="Read Only")
    accounting = create_user(
        username="Racuni", password=ACCOUNTING_PASSWORD, role="Accounting"
    )
    apply_session_for_user(admin)
    controller = SettingsController()
    backup = controller.backup_database()
    marker = "P0-RESTORE-MARKER"
    customer_repository.add(marker, "QA", "", "", "Ljubljana", "SI", "", "", "")
    assert customer_repository.search(marker)

    apply_session_for_user(reader)
    set_identity(
        user=reader["username"],
        role="Administrator",
        authenticated=True,
        user_id=reader["id"],
        clear_overrides=True,
    )
    with pytest.raises(PermissionError):
        controller.restore_database(backup, READER_PASSWORD)
    assert customer_repository.search(marker)

    apply_session_for_user(accounting)
    with pytest.raises(PermissionError, match="skrbniške"):
        controller.restore_database(backup, ACCOUNTING_PASSWORD)
    assert customer_repository.search(marker)

    apply_session_for_user(admin)
    with pytest.raises(PermissionError, match="Geslo"):
        controller.restore_database(backup, "WrongPass1x")
    assert customer_repository.search(marker)

    controller.restore_database(backup, ADMIN_PASSWORD)
    assert not customer_repository.search(marker)
    ok, _err = authenticate_credentials("Jure", ADMIN_PASSWORD, {})
    assert ok


def test_corrupt_warehouse_file_is_not_replaced(tmp_path):
    if not any(row[1] == "WH-P0-108" for row in article_repository.get_all()):
        article_repository.add("WH-P0-108", "P0 zaloga", "", "kos", 5.0, 22)
    article = next(row for row in article_repository.get_all() if row[1] == "WH-P0-108")
    path = tmp_path / "warehouse.json"
    original = "{not-json"
    path.write_text(original, encoding="utf-8")
    service = WarehouseService(path=path)

    with pytest.raises(WarehouseStoreError):
        service.stock_rows()
    with pytest.raises(WarehouseStoreError):
        service.add_movement(
            movement_type="Prevzem",
            article_id=int(article[0]),
            warehouse_id="main",
            quantity=4,
            user="QA",
        )
    with pytest.raises(WarehouseStoreError):
        service._save({"warehouses": [], "stock": {}, "movements": []})
    assert path.read_text(encoding="utf-8") == original

    path.write_text("[]", encoding="utf-8")
    with pytest.raises(WarehouseStoreError):
        service.add_movement(
            movement_type="Prevzem",
            article_id=int(article[0]),
            warehouse_id="main",
            quantity=4,
            user="QA",
        )
    assert path.read_text(encoding="utf-8") == "[]"


def test_unreadable_warehouse_file_is_not_replaced(tmp_path, monkeypatch):
    if not any(row[1] == "WH-P0-108" for row in article_repository.get_all()):
        article_repository.add("WH-P0-108", "P0 zaloga", "", "kos", 5.0, 22)
    article = next(row for row in article_repository.get_all() if row[1] == "WH-P0-108")
    path = tmp_path / "warehouse.json"
    payload = {
        "warehouses": [{"id": "main", "name": "Glavno skladišče"}],
        "stock": {"1": {"main": {"qty": 7, "reserved": 1, "min_qty": 0}}},
        "movements": [{"id": 1, "type": "Prevzem"}],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    original = path.read_bytes()
    service = WarehouseService(path=path)
    real_read = Path.read_text

    def fake_read(self, *args, **kwargs):
        if self == path:
            raise OSError("access denied")
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read)
    with pytest.raises(WarehouseStoreError):
        service.add_movement(
            movement_type="Izdaja",
            article_id=int(article[0]),
            warehouse_id="main",
            quantity=2,
            user="QA",
        )
    assert path.read_bytes() == original


def test_missing_warehouse_file_can_still_be_created(tmp_path):
    if not any(row[1] == "WH-P0-108" for row in article_repository.get_all()):
        article_repository.add("WH-P0-108", "P0 zaloga", "", "kos", 5.0, 22)
    article = next(row for row in article_repository.get_all() if row[1] == "WH-P0-108")
    path = tmp_path / "warehouse.json"
    service = WarehouseService(path=path)
    service.add_movement(
        movement_type="Prevzem",
        article_id=int(article[0]),
        warehouse_id="main",
        quantity=3,
        user="QA",
    )
    saved = json.loads(path.read_text(encoding="utf-8"))
    cell = saved["stock"][str(article[0])]["main"]
    assert cell["qty"] == 3
    assert path.with_name(path.name + ".tmp").exists() is False
