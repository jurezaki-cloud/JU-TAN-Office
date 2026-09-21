"""Document branding helpers — palette resolution and asset archival."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from reportlab.lib.colors import HexColor, white

from app.core.constants import DATA_DIR
from app.database.company_repository import (
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    DEFAULT_TABLE_HEADER,
)
from app.theme.colors import LightColors

_HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def normalize_hex(value: str, fallback: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return fallback
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if not _HEX.match(raw):
        return fallback
    return "#" + raw[1:].upper()


def resolve_palette(options: dict | None = None) -> dict:
    """Resolve ReportLab colors from PDF options (DB branding) with safe defaults."""
    colors = (options or {}).get("colors") or {}
    primary = normalize_hex(colors.get("primary"), DEFAULT_PRIMARY)
    accent = normalize_hex(colors.get("accent"), DEFAULT_ACCENT)
    table_header = normalize_hex(colors.get("table_header"), DEFAULT_TABLE_HEADER)
    return {
        "navy": HexColor(primary),
        "primary": HexColor(accent),
        "muted": HexColor(LightColors.SECONDARY),
        "border": HexColor(LightColors.BORDER),
        "table_header": HexColor(table_header),
        "surface": HexColor(LightColors.SURFACE),
        "white": white,
        "primary_hex": primary,
        "accent_hex": accent,
        "table_header_hex": table_header,
    }


def branding_dir() -> Path:
    folder = DATA_DIR / "branding"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def archive_branding_asset(source: str, kind: str) -> str:
    """
    Copy a user-selected image into DATA_DIR/branding for stable PDF paths.

    kind: logo | signature | stamp
    Returns the archived path string, or "" if source is empty/missing.
    """
    if not source:
        return ""
    src = Path(source)
    if not src.exists() or not src.is_file():
        return str(source)
    suffix = src.suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        suffix = ".png"
    target = branding_dir() / f"company_{kind}{suffix}"
    try:
        from app.core.security import ensure_inside

        target = ensure_inside(target, branding_dir())
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
        return str(target)
    except Exception:
        return str(source)
