"""Settings Center widgets.

Import concrete cards from their modules (e.g. ``license_card.LicenseCard``)
to avoid circular imports with ``settings_page`` / ``settings_controller``.
"""

from __future__ import annotations

__all__ = [
    "AboutCard",
    "AppearanceCard",
    "BackupCard",
    "CompanyCard",
    "LicenseCard",
    "NumberingCard",
    "PdfCard",
    "PrivacyCard",
    "SettingsHealthCard",
    "SettingsNav",
    "SettingsSectionHeader",
    "UpdateCard",
]


def __getattr__(name: str):
    if name == "AboutCard":
        from app.widgets.settings.about_card import AboutCard

        return AboutCard
    if name == "AppearanceCard":
        from app.widgets.settings.appearance_card import AppearanceCard

        return AppearanceCard
    if name == "BackupCard":
        from app.widgets.settings.backup_card import BackupCard

        return BackupCard
    if name == "CompanyCard":
        from app.widgets.settings.company_card import CompanyCard

        return CompanyCard
    if name == "LicenseCard":
        from app.widgets.settings.license_card import LicenseCard

        return LicenseCard
    if name == "NumberingCard":
        from app.widgets.settings.numbering_card import NumberingCard

        return NumberingCard
    if name == "PdfCard":
        from app.widgets.settings.pdf_card import PdfCard

        return PdfCard
    if name == "PrivacyCard":
        from app.widgets.settings.privacy_card import PrivacyCard

        return PrivacyCard
    if name == "SettingsHealthCard":
        from app.widgets.settings.settings_health_card import SettingsHealthCard

        return SettingsHealthCard
    if name == "SettingsNav":
        from app.widgets.settings.settings_nav import SettingsNav

        return SettingsNav
    if name == "SettingsSectionHeader":
        from app.widgets.settings.settings_section import SettingsSectionHeader

        return SettingsSectionHeader
    if name == "UpdateCard":
        from app.widgets.settings.update_card import UpdateCard

        return UpdateCard
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
