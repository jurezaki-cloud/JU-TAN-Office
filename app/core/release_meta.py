"""Release identity — single source for packaging metadata sync.

Runtime code reads APP_* / SCHEMA_VERSION from app.core.constants.
This module re-exports those values and packaging-only strings so
scripts/sync_release_metadata.py can regenerate Version.txt,
file_version_info.txt and packaging/version.iss without drift.
"""

from __future__ import annotations

from app.core.constants import (
    APP_AUTHOR,
    APP_BUILD,
    APP_CHANNEL,
    APP_NAME,
    APP_VERSION,
    SCHEMA_VERSION,
)

APP_PRODUCT = "JU-TAN Office Enterprise"
APP_EXE_NAME = "JU-TAN-Office"
APP_COPYRIGHT = f"(C) 2026 {APP_AUTHOR}"
APP_PUBLISHER_URL = "https://www.ju-tan.com"
APP_SUPPORT_URL = "https://www.ju-tan.com"
APP_UPDATES_URL = "https://www.ju-tan.com"
APP_SUPPORT_EMAIL = "support@ju-tan.com"
APP_ARCHITECTURE = "x64"
APP_RELEASE_DATE = "2026-09-12"

__all__ = [
    "APP_ARCHITECTURE",
    "APP_AUTHOR",
    "APP_BUILD",
    "APP_CHANNEL",
    "APP_COPYRIGHT",
    "APP_EXE_NAME",
    "APP_NAME",
    "APP_PRODUCT",
    "APP_PUBLISHER_URL",
    "APP_RELEASE_DATE",
    "APP_SUPPORT_EMAIL",
    "APP_SUPPORT_URL",
    "APP_UPDATES_URL",
    "APP_VERSION",
    "SCHEMA_VERSION",
]
