from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import Image, Spacer

from app.core.constants import BASE_DIR, DATA_DIR, RESOURCE_DIR

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


def bundled_logo_path() -> Path | None:
    """Full horizontal JU-TAN logo shipped with the app (source + PyInstaller)."""
    candidates = [
        RESOURCE_DIR / "logo.png",
        BASE_DIR / "resources" / "logo.png",
    ]
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "resources" / "logo.png")
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def archived_branding_logo() -> Path | None:
    """Recover logo archived under DATA_DIR/branding (stable user asset)."""
    folder = DATA_DIR / "branding"
    try:
        if not folder.is_dir():
            return None
    except OSError:
        return None
    for suffix in _IMAGE_SUFFIXES:
        candidate = folder / f"company_logo{suffix}"
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    try:
        for candidate in sorted(folder.glob("company_logo.*")):
            if candidate.is_file() and candidate.suffix.lower() in _IMAGE_SUFFIXES:
                return candidate
    except OSError:
        return None
    return None


def heal_logo_path(stored: str | None) -> str:
    """
    Return a readable logo path.

    Priority:
    1. stored path when the file still exists
    2. basename match inside DATA_DIR/branding (heals stale absolute installs)
    3. archived company_logo.* under DATA_DIR/branding
    4. empty string (caller may use bundled fallback)
    """
    raw = str(stored or "").strip()
    if raw:
        direct = Path(raw)
        try:
            if direct.is_file():
                return str(direct)
        except OSError:
            pass
        # Stale absolute path from a previous install → same basename in branding.
        branding = DATA_DIR / "branding" / direct.name
        try:
            if branding.is_file():
                return str(branding)
        except OSError:
            pass

    archived = archived_branding_logo()
    if archived is not None:
        return str(archived)
    return raw


def resolve_pdf_logo_path(company_logo: str | None) -> Path | None:
    """Company logo → archived branding → bundled resources/logo.png."""
    healed = heal_logo_path(company_logo)
    if healed:
        path = Path(healed)
        try:
            if path.is_file():
                return path
        except OSError:
            pass
    archived = archived_branding_logo()
    if archived is not None:
        return archived
    return bundled_logo_path()


def _existing_image_path(path: str) -> Path | None:
    """Resolve user assets and PyInstaller-bundled resources reliably."""
    if not path:
        return None

    raw = Path(path)
    candidates: list[Path] = [raw]

    # A selected branding asset is archived under the active DATA_DIR/branding
    # directory. Older installs can leave an absolute path pointing at a
    # previous install/profile, so recover the same archived filename there.
    if raw.is_absolute():
        candidates.append(DATA_DIR / "branding" / raw.name)
    else:
        # Prefer install/resource roots — never depend on the process CWD alone.
        candidates.append(BASE_DIR / raw)
        candidates.append(RESOURCE_DIR / raw.name)
        if raw.parts and raw.parts[0] == "resources":
            candidates.append(RESOURCE_DIR / Path(*raw.parts[1:]))
        candidates.append(Path(__file__).resolve().parents[2] / raw)
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            candidates.append(Path(bundle_root) / raw)
            if raw.name:
                candidates.append(Path(bundle_root) / "resources" / raw.name)

    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def pdf_image(path: str, max_width_mm: float = 42, max_height_mm: float = 22):
    resolved = _existing_image_path(path)
    if resolved is None:
        return None
    try:
        image = Image(str(resolved))
        width = float(image.imageWidth or 0)
        height = float(image.imageHeight or 0)
    except Exception:
        return None
    # Reject corrupt/degenerate assets instead of rendering a tiny fragment.
    if width <= 1 or height <= 1:
        return None
    max_w = max_width_mm * mm
    max_h = max_height_mm * mm
    scale = min(max_w / width, max_h / height, 1.0)
    image.drawWidth = width * scale
    image.drawHeight = height * scale
    image.hAlign = "LEFT"
    return image


def image_or_space(path: str, width_mm: float, height_mm: float):
    image = pdf_image(path, width_mm, height_mm)
    if image is not None:
        return image
    return Spacer(width_mm * mm, height_mm * mm)
