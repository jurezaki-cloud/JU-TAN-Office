"""SettingsPage must insert UsersCard / FreshZoneCard into the live layout."""

from __future__ import annotations

import pytest

from app.core.permissions import can
from app.core.session import session
from app.core.user_service import (
    apply_session_for_user,
    create_first_administrator,
    create_user,
    role_default_permission_keys,
)
from app.database.database import db
from app.database.user_repository import user_repository
from app.modules.settings.settings_controller import SETTINGS_PATH
from app.modules.settings.settings_page import SettingsPage
from app.widgets.settings.fresh_zone_card import FreshZoneCard
from app.widgets.settings.users_card import UsersCard

VALID_PASSWORD = "SecurePass1x"
VALID_PASSWORD_2 = "SecurePass2y"


def _wipe_users() -> None:
    user_repository.ensure_schema()
    with db.transaction() as conn:
        conn.execute("DELETE FROM user_permissions")
        conn.execute("DELETE FROM users")


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


def _grid_widgets(page: SettingsPage) -> list:
    widgets = []
    for i in range(page._grid.count()):
        item = page._grid.itemAt(i)
        if item is not None and item.widget() is not None:
            widgets.append(item.widget())
    return widgets


def test_first_admin_has_users_and_fresh_permissions():
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    keys = user_repository.get_permissions(admin["id"])
    assert "users" in keys
    assert "fresh" in keys
    apply_session_for_user(admin)
    assert can("users") is True
    assert can("fresh") is True


def test_settings_page_inserts_users_and_fresh_cards_for_admin(qt_app):
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    page = SettingsPage()
    page.resize(1200, 900)
    page.show()
    qt_app.processEvents()

    assert isinstance(page.users_card, UsersCard)
    assert isinstance(page.fresh_zone_card, FreshZoneCard)
    laid_out = _grid_widgets(page)
    assert page.users_card in laid_out
    assert page.fresh_zone_card in laid_out
    assert page.users_card.isVisibleTo(page)
    assert page.fresh_zone_card.isVisibleTo(page)
    assert page.users_card.btn_new.isEnabled()
    assert page.users_card.btn_edit.isEnabled()
    assert page.users_card.btn_reset.isEnabled()
    assert page.users_card.btn_remove.isEnabled()
    assert page.users_card.table.rowCount() >= 1
    page.close()


def test_users_and_fresh_cards_hidden_without_permission(qt_app):
    admin = create_first_administrator("Jure", VALID_PASSWORD)
    apply_session_for_user(admin)
    sales = create_user(
        username="Tanja",
        password=VALID_PASSWORD_2,
        role="Sales",
        permissions=role_default_permission_keys("Sales"),
    )
    apply_session_for_user(sales)
    assert can("users") is False
    assert can("fresh") is False

    page = SettingsPage()
    page.resize(1200, 900)
    page.show()
    qt_app.processEvents()

    # Cards remain in the layout tree but RBAC hides them.
    assert page.users_card in _grid_widgets(page)
    assert page.fresh_zone_card in _grid_widgets(page)
    assert not page.users_card.isVisibleTo(page)
    assert not page.fresh_zone_card.isVisibleTo(page)

    # Switching identity + refresh must update visibility without restart.
    apply_session_for_user(admin)
    page.refresh()
    qt_app.processEvents()
    assert page.users_card.isVisibleTo(page)
    assert page.fresh_zone_card.isVisibleTo(page)
    page.close()
