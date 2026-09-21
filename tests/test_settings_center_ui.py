"""Settings Center UI redesign — navigation, health, sections (UI only)."""

from __future__ import annotations

from app.core.session import session
from app.modules.settings.settings_page import SettingsPage
from app.widgets.settings.license_card import LicenseCard
from app.widgets.settings.settings_health_card import SettingsHealthCard
from app.widgets.settings.settings_nav import SETTINGS_NAV_ITEMS, SettingsNav


def _grid_widgets(page: SettingsPage) -> list:
    widgets = []
    for i in range(page._grid.count()):
        item = page._grid.itemAt(i)
        if item is not None and item.widget() is not None:
            widgets.append(item.widget())
    return widgets


def _finish_scroll(page: SettingsPage, qt_app) -> None:
    """Complete any in-flight smooth-scroll animation for deterministic asserts."""
    anim = page._scroll_anim
    if anim is not None:
        anim.setCurrentTime(anim.duration())
        qt_app.processEvents()
    qt_app.processEvents()


def _ensure_settings_data(page: SettingsPage, qt_app) -> None:
    """Flush deferred shell→data load after show()."""
    if not page._data_loaded:
        page.refresh()
    qt_app.processEvents()


def _section_offset_from_top(page: SettingsPage, key: str) -> int:
    target = page._anchor_for(key)
    assert target is not None
    y = target.mapTo(page._canvas, target.rect().topLeft()).y()
    return y - page._scroll.verticalScrollBar().value()


def test_settings_center_shell_and_nav(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    page.resize(1280, 900)
    page.show()
    qt_app.processEvents()
    _ensure_settings_data(page, qt_app)

    assert page.objectName() == "SettingsPage"
    assert isinstance(page.nav, SettingsNav)
    assert isinstance(page.health_card, SettingsHealthCard)
    assert page.header.title.text() == "Nastavitve"
    assert page.nav.isVisibleTo(page)
    assert page.health_card.isVisibleTo(page)

    laid_out = _grid_widgets(page)
    assert page.health_card in laid_out
    assert page.license_card in laid_out
    assert isinstance(page.license_card, LicenseCard)

    page.nav.select("license")
    page._on_category("license")
    _finish_scroll(page, qt_app)
    assert page.nav._active == "license"
    assert _section_offset_from_top(page, "license") <= 48

    page.close()


def test_settings_nav_scrolls_every_category_to_section(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    page.resize(1280, 820)
    page.show()
    qt_app.processEvents()
    _ensure_settings_data(page, qt_app)

    expected = {
        "overview": page.section_overview,
        "documents": page.section_documents,
        "appearance": page.section_appearance,
        "modules": page.travel_card,  # wide mode hides modules header
        "security": page.section_security,
        "users": page.section_users,
        "backup": page.section_backup,
        "license": page.section_license,
        "updates": page.section_updates,
        "privacy": page.section_privacy,
        "about": page.section_about,
        "danger": page.section_danger,
    }

    for key, _label, _icon, _group in SETTINGS_NAV_ITEMS:
        assert key in page._anchors
        anchor = page._anchor_for(key)
        assert anchor is expected[key]
        assert anchor.property("settingsAnchor") == key or key == "modules"

        page._scroll.verticalScrollBar().setValue(0)
        qt_app.processEvents()

        page.nav._buttons[key].click()
        qt_app.processEvents()
        _finish_scroll(page, qt_app)

        assert page.nav._active == key
        offset = _section_offset_from_top(page, key)
        assert offset <= 48, f"{key} landed {offset}px from top (want near top)"

    page.close()


def test_settings_nav_follows_manual_scroll(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    page.resize(1280, 820)
    page.show()
    qt_app.processEvents()
    _ensure_settings_data(page, qt_app)

    target = page.section_security
    y = target.mapTo(page._canvas, target.rect().topLeft()).y()
    page._nav_programmatic = False
    page._scroll.verticalScrollBar().setValue(max(0, y - 12))
    qt_app.processEvents()

    assert page.nav._active == "security"
    page.close()


def test_settings_health_refresh_without_license(qt_app, monkeypatch):
    import app.widgets.settings.settings_health_card as health_mod

    monkeypatch.setattr(health_mod.LicenseState, "load", classmethod(lambda cls: None))
    card = SettingsHealthCard()
    card.refresh(about={"version": "1.0.0 GOLD"}, appearance={"theme": "light"})
    assert "Ni aktivirana" in card.kpi_license.value.text()
    assert card.lbl_summary.property("kind") in {"ok", "warn", "bad"}
    card.close()
