"""SettingsPage must insert LicenseCard into the live layout."""

from __future__ import annotations

from app.core.session import session
from app.modules.settings.settings_page import SettingsPage
from app.widgets.settings.license_card import LicenseCard


def _grid_widgets(page: SettingsPage) -> list:
    widgets = []
    for i in range(page._grid.count()):
        item = page._grid.itemAt(i)
        if item is not None and item.widget() is not None:
            widgets.append(item.widget())
    return widgets


def test_settings_page_inserts_license_card(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    page.resize(1200, 900)
    page.show()
    qt_app.processEvents()

    assert isinstance(page.license_card, LicenseCard)
    laid_out = _grid_widgets(page)
    assert page.license_card in laid_out
    assert page.license_card.isVisibleTo(page)
    assert page.license_card.btn_check.text() == "Preveri licenco"
    page.close()


def test_license_card_refresh_without_state(qt_app, monkeypatch):
    import app.widgets.settings.license_card as license_card_mod

    monkeypatch.setattr(license_card_mod.LicenseState, "load", classmethod(lambda cls: None))
    card = LicenseCard()
    card.refresh()
    assert card.lbl_status.text() == "Ni aktivirana"
    assert card.btn_check.isEnabled()
    assert not card.btn_deactivate.isEnabled()
    assert hasattr(card, "lbl_plan")
    assert hasattr(card, "lbl_expiry")
    assert hasattr(card, "lbl_seats")
    card.close()
