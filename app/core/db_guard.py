"""Zaščita SQLite: integrity, FK, WAL, VACUUM, preverjanje kopije."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from app.core.constants import DATABASE_PATH, DATA_DIR
from app.core.logger import logger
from app.database.database import db

VACUUM_MARK = DATA_DIR / "last_vacuum.txt"
VACUUM_EVERY_SEC = 7 * 24 * 3600


def integrity_ok(path: Path | None = None) -> bool:
    target = Path(path or DATABASE_PATH)
    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        row = conn.execute("PRAGMA integrity_check").fetchone()
        return bool(row) and row[0] == "ok"
    finally:
        conn.close()


def verify_backup(path: Path) -> bool:
    return integrity_ok(path)


def ensure_runtime() -> None:
    conn = db.connect()
    try:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()
        wal = conn.execute("PRAGMA journal_mode").fetchone()
        logger.info("SQLite foreign_keys=%s journal=%s", fk[0] if fk else "?", wal[0] if wal else "?")
        if not integrity_ok():
            logger.error("integrity_check ni uspel")
            raise sqlite3.DatabaseError("Baza ni konsistentna.")
    finally:
        conn.close()


def maybe_vacuum() -> bool:
    now = time.time()
    last = 0.0
    if VACUUM_MARK.exists():
        try:
            last = float(VACUUM_MARK.read_text(encoding="utf-8").strip() or 0)
        except ValueError:
            last = 0.0
    if now - last < VACUUM_EVERY_SEC:
        return False
    conn = db.connect()
    try:
        conn.execute("VACUUM")
        raw = object.__getattribute__(conn, "_raw")
        raw.commit()
    finally:
        conn.close()
    VACUUM_MARK.write_text(str(now), encoding="utf-8")
    logger.info("SQLite VACUUM")
    return True
