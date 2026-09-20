"""Nastavitve: atomski zapis in obnovitev poškodovanega JSON."""

from app.core.constants import DATA_DIR
from app.modules.settings.settings_controller import SETTINGS_PATH, SettingsController, default_settings


def test_settings_roundtrip_and_corrupt_recovery():
    controller = SettingsController()
    extras = default_settings()
    extras["swift"] = "LJBASI2X"
    controller.save_extras(extras)
    loaded = controller.load_extras()
    assert loaded["swift"] == "LJBASI2X"
    SETTINGS_PATH.write_text("{not-json", encoding="utf-8")
    recovered = controller.load_extras()
    assert recovered["appearance"]["theme"] == "light"
    assert DATA_DIR.exists()
