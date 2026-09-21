"""Commercial Foundation P0 — License / Update / Privacy / About UI (UI only)."""

from __future__ import annotations

from app.core.session import session
from app.modules.settings.settings_page import SettingsPage
from app.widgets.settings.about_card import AboutCard, SUPPORT_EMAIL
from app.widgets.settings.license_card import LicenseCard
from app.widgets.settings.privacy_card import PrivacyCard
from app.widgets.settings.update_card import UpdateCard


def _grid_widgets(page: SettingsPage) -> list:
    widgets = []
    for i in range(page._grid.count()):
        item = page._grid.itemAt(i)
        if item is not None and item.widget() is not None:
            widgets.append(item.widget())
    return widgets


def test_commercial_foundation_cards_in_settings(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    page.resize(1280, 900)
    page.show()
    qt_app.processEvents()

    laid_out = _grid_widgets(page)
    assert isinstance(page.license_card, LicenseCard)
    assert isinstance(page.update_card, UpdateCard)
    assert isinstance(page.privacy_card, PrivacyCard)
    assert isinstance(page.about_card, AboutCard)
    assert page.license_card in laid_out
    assert page.update_card in laid_out
    assert page.privacy_card in laid_out
    assert page.about_card in laid_out

    assert "updates" in page._anchors
    assert "privacy" in page._anchors
    assert page.nav._buttons["updates"].isVisibleTo(page)
    assert page.nav._buttons["privacy"].isVisibleTo(page)

    page.close()


def test_license_center_shows_commercial_fields(qt_app, monkeypatch):
    import app.widgets.settings.license_card as license_card_mod

    monkeypatch.setattr(license_card_mod.LicenseState, "load", classmethod(lambda cls: None))
    monkeypatch.setattr(license_card_mod, "_plan_label", lambda: "")
    monkeypatch.setattr(license_card_mod, "_expiry_label", lambda: "")

    card = LicenseCard()
    card.refresh()

    assert card.lbl_status.text() == "Ni aktivirana"
    assert card.lbl_plan.text() == "—"
    assert card.lbl_expiry.text() == "—"
    assert card.lbl_seats.text() == "—"
    assert card.lbl_verify.text() == "Ni preverjeno"
    assert card.btn_check.text() == "Preveri licenco"
    assert card.btn_deactivate.text() == "Deaktiviraj napravo"
    assert not card.btn_deactivate.isEnabled()
    card.close()


def test_update_center_check_shows_empty_state(qt_app, monkeypatch):
    import app.core.update as update_core

    monkeypatch.setattr(update_core, "check_for_update", lambda: None)
    card = UpdateCard()
    card.check_updates()
    assert card.empty_state.isVisibleTo(card)
    assert card.lbl_status.text() == "Ni posodobitev"
    assert card.btn_check.text() == "Preveri posodobitve"
    card.close()


def test_privacy_card_actions_present(qt_app):
    card = PrivacyCard()
    assert "lokalno" in card.lbl_privacy_info.text().lower() or "podatke" in card.lbl_privacy_info.text().lower()
    assert card.btn_export.text() == "Izvozi podatke"
    assert card.btn_policy.text() == "Politika zasebnosti"
    assert card.btn_manage.text() == "Upravljanje podatkov"
    card.close()


def test_about_card_branding(qt_app):
    card = AboutCard()
    card.set_values(
        {
            "app": "JU-TAN Office Enterprise",
            "edition": "Enterprise GOLD",
            "version": "1.0.0 GOLD",
            "python": "3.12",
            "qt": "6.0",
            "sqlite": "3.0",
            "build": "RELEASE",
            "copyright": "© 2026 JU-TAN Studio",
        }
    )
    assert "JU-TAN" in card.app_name.text()
    assert card.lbl_company.text() == "JU-TAN Studio"
    assert card.lbl_support.text() == SUPPORT_EMAIL
    assert card.lbl_version.text() == "1.0.0 GOLD"
    assert card.btn_website.isEnabled()
    assert card.btn_support.isEnabled()
    card.close()
