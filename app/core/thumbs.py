"""Predpomnilnik sličic in čiščenje začasnih datotek."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from app.core.constants import TEMP_DIR

THUMB_DIR = TEMP_DIR / "thumbs"
ATTACH_DIR = TEMP_DIR / "attachments"
MAX_AGE_SECONDS = 7 * 24 * 3600


def thumb_path(source: Path, size: int = 260) -> Path:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(f"{source.resolve()}|{source.stat().st_mtime_ns}|{size}".encode()).hexdigest()
    return THUMB_DIR / f"{digest}.png"


def cached_pixmap(source: Path, size: int = 260):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap

    path = Path(source)
    if not path.exists():
        return QPixmap()
    cache = thumb_path(path, size)
    if cache.exists():
        pix = QPixmap(str(cache))
        if not pix.isNull():
            return pix
    pix = QPixmap(str(path))
    if pix.isNull():
        return pix
    scaled = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.FastTransformation)
    scaled.save(str(cache), "PNG")
    return scaled


def cleanup_temp(*, max_age: int = MAX_AGE_SECONDS) -> int:
    """Izbriši stare datoteke v Temp (ne baze, ne backupov)."""
    removed = 0
    now = time.time()
    root = TEMP_DIR
    if not root.exists():
        return 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            if now - path.stat().st_mtime > max_age:
                path.unlink()
                removed += 1
        except OSError:
            continue
    return removed
