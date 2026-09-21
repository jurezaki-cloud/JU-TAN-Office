from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import Image, Spacer


def _existing_image_path(path: str) -> Path | None:
    """Resolve user assets and PyInstaller-bundled resources reliably."""
    if not path:
        return None

    raw = Path(path)
    candidates = [raw]
    if not raw.is_absolute():
        # Source checkout / normal Python execution.
        candidates.append(Path(__file__).resolve().parents[2] / raw)
        # PyInstaller one-folder/one-file extraction root.
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            candidates.append(Path(bundle_root) / raw)

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
    return image


def image_or_space(path: str, width_mm: float, height_mm: float):
    image = pdf_image(path, width_mm, height_mm)
    if image is not None:
        return image
    return Spacer(width_mm * mm, height_mm * mm)
