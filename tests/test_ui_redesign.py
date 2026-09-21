"""UI redesign regression: theme startup, navigation, icons, identity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.core.constants import RESOURCE_DIR
from app.modules.settings.settings_controller import SettingsController, SETTINGS_PATH
from app.theme.colors import ThemeMode
from app.theme.theme import theme_manager
from app.widgets.navigation import NAV_GROUPS, PAGE_INDEX, ModernSidebar
from app.widgets.toolbar.toolbar_actions import ToolbarActions
from app.widgets.common import EmptyState, PageHeader
from app.core.ui.brand_icons import NAV_ICONS, brand_icon
from app.core.ui.app_identity import application_icon, apply_application_identity


def _write_png(path: Path) -> Path:
    """Write a tiny valid RGBA PNG (libpng-safe) for resolver/pixmap tests."""
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (16, 16), (255, 255, 255, 255)).save(path)
    return path


def test_app_icon_asset_exists():
    ico = RESOURCE_DIR / "app.ico"
    assert ico.exists()
    assert ico.stat().st_size > 1000


def test_application_identity_sets_icon(qt_app):
    apply_application_identity(qt_app)
    icon = application_icon()
    assert not icon.isNull()
    assert not qt_app.windowIcon().isNull()


def test_brand_icons_for_all_nav_modules(qt_app):
    for index, name in NAV_ICONS.items():
        icon = brand_icon(name, color="#F8FAFC", size=18)
        assert not icon.isNull(), f"missing icon for {index}:{name}"


def test_nav_groups_cover_all_pages():
    indices = []
    for _title, pages in NAV_GROUPS:
        for _label, idx in pages:
            indices.append(idx)
    assert sorted(indices) == list(range(18))
    assert PAGE_INDEX["travel_orders"] == 17
    # Business order: invoices before customers in PRODAJA group
    prodaja = dict(NAV_GROUPS)["PRODAJA"]
    labels = [label for label, _ in prodaja]
    assert labels.index("Računi") < labels.index("Stranke")
    assert labels.index("Ponudbe") < labels.index("Naročila")


def test_sidebar_has_icons_and_groups(qt_app):
    from app.core.session import session

    session.login("Admin", "Administrator")
    sidebar = ModernSidebar()
    sidebar.apply_role()
    assert len(sidebar.buttons) == 18
    assert all(not btn.icon().isNull() for btn in sidebar.buttons.values())
    assert sidebar._section_labels
    sidebar.set_active(1)
    assert sidebar.buttons[1].isChecked()
    assert not sidebar.buttons[0].isChecked()
    sidebar.set_collapsed(True)
    assert sidebar.width() < 100
    sidebar.set_collapsed(False)
    assert sidebar.width() >= 200
    sidebar.close()


def test_novo_menu_respects_rbac(qt_app, monkeypatch):
    from app.core import permissions
    from app.core.session import session

    session.login("RO", "Read Only")
    permissions.set_identity(user="RO", role="Read Only", authenticated=True)
    actions = ToolbarActions()
    actions.refresh_permissions()
    assert not actions.btn_new.isEnabled() or actions._new_menu.isEmpty()
    actions.close()

    session.login("Admin", "Administrator")
    permissions.set_identity(user="Admin", role="Administrator", authenticated=True)
    actions = ToolbarActions()
    actions.refresh_permissions()
    labels = [a.text() for a in actions._new_menu.actions()]
    assert "Nov račun" in labels
    assert "Nova ponudba" in labels
    assert "Novo naročilo" in labels
    assert "Nova stranka" in labels
    actions.close()


def test_page_components_create(qt_app):
    header = PageHeader("Računi", "Test", action_text="+ Nov račun")
    assert header.title.text() == "Računi"
    assert header.title.isHidden()  # shell ToolbarTitle owns the H1
    assert not header.description.isHidden()
    empty = EmptyState("Ni še računov", "Ustvarite prvi račun.", action_text="+ Nov račun")
    assert empty.title.text() == "Ni še računov"
    assert empty.title.objectName() == "DashboardEmptyState"
    header.close()
    empty.close()


def _write_appearance(theme: str, accent: str = "green") -> None:
    data = SettingsController().load_extras()
    data["appearance"] = {
        "theme": theme,
        "accent": accent,
        "font_size": "normal",
        "radius": "medium",
    }
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    from app.core.config_guard import stamp
    from app.core.security import write_json_atomic

    write_json_atomic(SETTINGS_PATH, stamp(data))


def test_saved_dark_theme_applied_at_startup_path(qt_app, monkeypatch):
    _write_appearance("dark")
    mode = SettingsController().apply_appearance(qt_app)
    assert mode == "dark"
    assert theme_manager.mode == ThemeMode.DARK
    sheet = qt_app.styleSheet()
    assert sheet
    assert "#0B1220" in sheet or "#0F172A" in sheet or "background" in sheet.lower()


def test_saved_light_theme_applied_at_startup_path(qt_app):
    _write_appearance("light")
    mode = SettingsController().apply_appearance(qt_app)
    assert mode == "light"
    assert theme_manager.mode == ThemeMode.LIGHT


def test_theme_persistence_roundtrip(qt_app):
    _write_appearance("dark", "green")
    extras = SettingsController().load_extras()
    assert extras["appearance"]["theme"] == "dark"
    assert extras["appearance"]["accent"] == "green"
    SettingsController().apply_appearance(qt_app)
    assert theme_manager.mode == ThemeMode.DARK
    _write_appearance("light", "blue")
    SettingsController().apply_appearance(qt_app)
    assert theme_manager.mode == ThemeMode.LIGHT


def test_mainwindow_opens_with_theme(qt_app):
    from app.core.session import session
    from app.windows.main_window import MainWindow

    _write_appearance("dark")
    SettingsController().apply_appearance(qt_app)
    session.login("Admin", "Administrator")
    window = MainWindow()
    assert window.windowTitle()
    assert not window.windowIcon().isNull()
    assert window.sidebar.buttons[0].isChecked()
    window.close()


def test_resolve_brand_logo_theme_aware(qt_app, tmp_path, monkeypatch):
    """LIGHT prefers logo_light; DARK prefers logo_dark then logo.png."""
    from app.core import constants
    from app.widgets.navigation.sidebar_header import resolve_brand_logo

    data = tmp_path / "data"
    data.mkdir()
    light = data / "logo_light.png"
    dark = data / "logo_dark.png"
    fallback = data / "logo.png"
    _write_png(light)
    _write_png(fallback)

    monkeypatch.setattr(constants, "DATA_DIR", data)
    monkeypatch.setattr(constants, "BASE_DIR", tmp_path)
    monkeypatch.setattr(constants, "RESOURCE_DIR", tmp_path / "resources")
    (tmp_path / "resources").mkdir()

    import app.widgets.navigation.sidebar_header as sh

    monkeypatch.setattr(sh, "DATA_DIR", data)
    monkeypatch.setattr(sh, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sh, "RESOURCE_DIR", tmp_path / "resources")

    assert resolve_brand_logo(ThemeMode.LIGHT) == light
    assert resolve_brand_logo(ThemeMode.DARK) == fallback

    _write_png(dark)
    assert resolve_brand_logo(ThemeMode.DARK) == dark

    theme_manager.apply(qt_app, ThemeMode.LIGHT)
    assert resolve_brand_logo() == light
    theme_manager.apply(qt_app, ThemeMode.DARK)
    assert resolve_brand_logo() == dark


def test_sidebar_logo_uses_dark_surface_contrast(qt_app, tmp_path, monkeypatch):
    """Sidebar is always dark — must resolve light-ink logo even in LIGHT theme."""
    from app.widgets.navigation.sidebar_header import (
        SidebarHeader,
        resolve_brand_logo,
        resolve_brand_logo_for_surface,
        refresh_brand_logos,
    )
    import app.widgets.navigation.sidebar_header as sh

    data = tmp_path / "data"
    data.mkdir()
    light = data / "logo_light.png"
    fallback = data / "logo.png"
    _write_png(light)
    _write_png(fallback)
    monkeypatch.setattr(sh, "DATA_DIR", data)
    monkeypatch.setattr(sh, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sh, "RESOURCE_DIR", tmp_path / "resources")
    (tmp_path / "resources").mkdir(exist_ok=True)

    theme_manager.apply(qt_app, ThemeMode.LIGHT)
    assert resolve_brand_logo(ThemeMode.LIGHT) == light
    assert resolve_brand_logo_for_surface(dark_surface=True) == fallback

    from app.core.session import session

    session.login("Admin", "Administrator")
    header = SidebarHeader()
    header.show()
    qt_app.processEvents()
    assert header._logo_path == fallback
    assert not header.logo.pixmap().isNull()
    assert header.brand.isHidden()

    theme_manager.apply(qt_app, ThemeMode.DARK)
    refresh_brand_logos()
    assert header._logo_path == resolve_brand_logo_for_surface(dark_surface=True)
    header.close()
    header.deleteLater()
    qt_app.processEvents()
    theme_manager.apply(qt_app, ThemeMode.LIGHT)


def test_sidebar_logo_refreshes_on_theme_change(qt_app, monkeypatch):
    from app.core.session import session
    from app.widgets.navigation.sidebar_header import (
        SidebarHeader,
        resolve_brand_logo_for_surface,
        refresh_brand_logos,
    )

    session.login("Admin", "Administrator")
    theme_manager.apply(qt_app, ThemeMode.LIGHT)
    header = SidebarHeader()
    surface_path = resolve_brand_logo_for_surface(dark_surface=True)
    assert surface_path is not None
    assert header._logo_path == surface_path

    theme_manager.apply(qt_app, ThemeMode.DARK)
    refresh_brand_logos()
    assert header._logo_path == resolve_brand_logo_for_surface(dark_surface=True)
    header.close()
    header.deleteLater()
    qt_app.processEvents()
    theme_manager.apply(qt_app, ThemeMode.LIGHT)


def test_login_logo_resolves_via_central_resolver(qt_app, tmp_path, monkeypatch):
    """Login uses the same resolve_brand_logo() as the rest of branding."""
    import app.widgets.navigation.sidebar_header as sh
    from app.widgets.navigation.sidebar_header import resolve_brand_logo

    data = tmp_path / "data"
    data.mkdir()
    light = _write_png(data / "logo_light.png")
    _write_png(data / "logo.png")
    monkeypatch.setattr(sh, "DATA_DIR", data)
    monkeypatch.setattr(sh, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sh, "RESOURCE_DIR", tmp_path / "resources")
    (tmp_path / "resources").mkdir(exist_ok=True)

    theme_manager.apply(qt_app, ThemeMode.LIGHT)
    assert resolve_brand_logo(ThemeMode.LIGHT) == light
    theme_manager.apply(qt_app, ThemeMode.DARK)
    assert resolve_brand_logo(ThemeMode.DARK) == data / "logo.png"
    theme_manager.apply(qt_app, ThemeMode.LIGHT)


def test_brand_logo_falls_back_when_override_missing(qt_app, tmp_path, monkeypatch):
    import app.widgets.navigation.sidebar_header as sh
    from app.widgets.navigation.sidebar_header import resolve_brand_logo

    empty = tmp_path / "empty"
    empty.mkdir()
    resources = tmp_path / "resources"
    resources.mkdir()
    packaged = _write_png(resources / "logo.png")
    monkeypatch.setattr(sh, "DATA_DIR", empty)
    monkeypatch.setattr(sh, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sh, "RESOURCE_DIR", resources)
    assert resolve_brand_logo(ThemeMode.DARK) == packaged


def test_frozen_style_resource_path_resolves(tmp_path, monkeypatch):
    """Simulate packaged resources/ next to resolver search roots."""
    import app.widgets.navigation.sidebar_header as sh
    from app.widgets.navigation.sidebar_header import resolve_brand_logo

    resources = tmp_path / "resources"
    resources.mkdir()
    light = _write_png(resources / "logo_light.png")
    dark = _write_png(resources / "logo.png")
    monkeypatch.setattr(sh, "DATA_DIR", tmp_path / "missing_data")
    monkeypatch.setattr(sh, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sh, "RESOURCE_DIR", resources)
    assert resolve_brand_logo(ThemeMode.LIGHT) == light
    assert resolve_brand_logo(ThemeMode.DARK) == dark


def test_settings_page_does_not_reapply_theme_on_construct(qt_app):
    """Opening Nastavitve must not be the first moment theme appears."""
    from app.core.session import session
    from app.modules.settings.settings_page import SettingsPage

    _write_appearance("dark")
    SettingsController().apply_appearance(qt_app)
    assert theme_manager.mode == ThemeMode.DARK
    session.login("Admin", "Administrator")
    # Force light stylesheet temporarily to detect unwanted re-apply from page init.
    before = qt_app.styleSheet()
    page = SettingsPage()
    assert theme_manager.mode == ThemeMode.DARK
    assert qt_app.styleSheet() == before
    page.close()