"""Settings P0 — deferred load + Save/Cancel persistence."""

from __future__ import annotations

from app.core.session import session
from app.database.company_repository import company_repository
from app.modules.settings.settings_controller import SettingsController
from app.modules.settings.settings_page import SettingsPage


def _load(page: SettingsPage, qt_app) -> None:
    page.show()
    qt_app.processEvents()
    if not page._data_loaded:
        page.refresh()
    qt_app.processEvents()


def test_settings_shell_defers_data_until_refresh(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    assert page._data_loaded is False
    assert page.defers_initial_refresh is True
    assert page.btn_save.isEnabled() is False
    assert page.btn_cancel.isEnabled() is False
    page.close()


def test_settings_save_persists_numbering_security_travel(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    ctrl = SettingsController()
    extras = ctrl.load_extras()
    extras["numbering"] = {
        **(extras.get("numbering") or {}),
        "order": {
            "prefix": "TST",
            "start": 10,
            "length": 5,
            "yearly_reset": True,
        },
    }
    extras["session_timeout_min"] = 45
    extras["travel_orders"] = {"mileage_rate": 0.43, "domestic_per_diem": 21.5}
    ctrl.save_extras(extras)

    page = SettingsPage()
    page.resize(1200, 800)
    _load(page, qt_app)

    assert page.numbering_card.values()["order"]["prefix"] == "TST"
    assert page.security_card.timeout.value() == 45
    assert abs(page.travel_card.mileage.value() - 0.43) < 1e-6

    page.numbering_card.rows["order"]["prefix"].setText("SAV")
    page.security_card.timeout.setValue(90)
    page.travel_card.mileage.setValue(0.55)
    page.travel_card.per_diem.setValue(30.0)
    qt_app.processEvents()
    assert page.is_dirty()
    assert page.btn_save.isEnabled()

    page._save()
    qt_app.processEvents()
    assert not page.is_dirty()
    page.close()

    page2 = SettingsPage()
    _load(page2, qt_app)
    assert page2.numbering_card.values()["order"]["prefix"] == "SAV"
    assert page2.security_card.timeout.value() == 90
    assert abs(page2.travel_card.mileage.value() - 0.55) < 1e-6
    assert abs(page2.travel_card.per_diem.value() - 30.0) < 1e-6
    page2.close()


def test_settings_invoice_offer_prefix_persists_after_reopen(qt_app):
    """Change → save → close → reopen must keep invoice/offer prefixes."""
    session.login("Administrator", "Administrator")
    session.locked = False

    # Stale company prefixes must not win over the last saved settings.json value.
    company_repository.update_document_prefixes("OLD", "OLD")

    page = SettingsPage()
    page.resize(1200, 800)
    _load(page, qt_app)

    page.numbering_card.rows["invoice"]["prefix"].setText("INVX")
    page.numbering_card.rows["offer"]["prefix"].setText("OFFX")
    qt_app.processEvents()
    assert page.is_dirty()

    page._save()
    qt_app.processEvents()
    assert not page.is_dirty()
    page.close()

    # settings.json is SoT; company is mirrored for document numbering.
    extras = SettingsController().load_extras()
    assert extras["numbering"]["invoice"]["prefix"] == "INVX"
    assert extras["numbering"]["offer"]["prefix"] == "OFFX"
    company = company_repository.get_company()
    assert company[16] == "INVX"
    assert company[17] == "OFFX"

    page2 = SettingsPage()
    _load(page2, qt_app)
    values = page2.numbering_card.values()
    assert values["invoice"]["prefix"] == "INVX"
    assert values["offer"]["prefix"] == "OFFX"
    page2.close()


def test_settings_prefix_not_overlaid_by_stale_company(qt_app):
    """load_bundle must not replace saved settings prefixes with company values."""
    session.login("Administrator", "Administrator")
    session.locked = False
    ctrl = SettingsController()
    extras = ctrl.load_extras()
    extras["numbering"] = {
        **(extras.get("numbering") or {}),
        "invoice": {
            **(extras.get("numbering") or {}).get("invoice", {}),
            "prefix": "SAVED",
        },
        "offer": {
            **(extras.get("numbering") or {}).get("offer", {}),
            "prefix": "KEEP",
        },
    }
    ctrl.save_extras(extras)
    company_repository.update_document_prefixes("STALE", "STALE")

    bundle = ctrl.load_bundle()
    assert bundle["extras"]["numbering"]["invoice"]["prefix"] == "SAVED"
    assert bundle["extras"]["numbering"]["offer"]["prefix"] == "KEEP"
    # Operational mirror repaired to match settings SoT.
    company = company_repository.get_company()
    assert company[16] == "SAVED"
    assert company[17] == "KEEP"


def test_settings_legacy_company_prefix_seeds_defaults(qt_app):
    """If settings still has shipped defaults, seed once from company."""
    session.login("Administrator", "Administrator")
    session.locked = False
    ctrl = SettingsController()
    extras = ctrl.load_extras()
    extras["numbering"] = {
        **(extras.get("numbering") or {}),
        "invoice": {
            **(extras.get("numbering") or {}).get("invoice", {}),
            "prefix": "RAC",
        },
        "offer": {
            **(extras.get("numbering") or {}).get("offer", {}),
            "prefix": "PON",
        },
    }
    ctrl.save_extras(extras)
    company_repository.update_document_prefixes("LEGACY", "LEGOF")

    bundle = ctrl.load_bundle()
    assert bundle["extras"]["numbering"]["invoice"]["prefix"] == "LEGACY"
    assert bundle["extras"]["numbering"]["offer"]["prefix"] == "LEGOF"
    # Seed is persisted so later loads stay stable without company overlay.
    reloaded = ctrl.load_extras()
    assert reloaded["numbering"]["invoice"]["prefix"] == "LEGACY"
    assert reloaded["numbering"]["offer"]["prefix"] == "LEGOF"


def test_settings_cancel_discards_confirmable_changes(qt_app):
    session.login("Administrator", "Administrator")
    session.locked = False
    page = SettingsPage()
    _load(page, qt_app)
    before = page.security_card.timeout.value()
    page.security_card.timeout.setValue(before + 15 if before < 200 else before - 15)
    assert page.is_dirty()
    page._reset()
    qt_app.processEvents()
    assert page.security_card.timeout.value() == before
    assert not page.is_dirty()
    page.close()
