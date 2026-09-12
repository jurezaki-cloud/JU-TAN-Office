"""Centralno logiranje JU-TAN Office Enterprise."""

from __future__ import annotations

import gzip
import logging
import os
import shutil
import sys
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from app.core.constants import LOG_DIR, LOG_FILE

SESSION_USER = os.environ.get("USERNAME") or os.environ.get("USER") or "Administrator"

logger = logging.getLogger("JU-TAN Office")
logger.setLevel(logging.INFO)


class _Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "user"):
            record.user = SESSION_USER
        return super().format(record)


def _gzip_rotator(source: str, dest: str) -> None:
    with open(source, "rb") as incoming, gzip.open(dest, "wb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
    os.remove(source)


def _gzip_namer(name: str) -> str:
    return name + ".gz"


def cleanup_old_logs(*, keep_days: int = 30) -> int:
    removed = 0
    root = Path(LOG_DIR)
    if not root.exists():
        return 0
    import time

    cutoff = time.time() - keep_days * 86400
    for path in root.glob("*.log*"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            continue
    return removed


if not logger.handlers:
    formatter = _Formatter("%(asctime)s | %(levelname)s | %(user)s | %(message)s")
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2_000_000,
        backupCount=14,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.rotator = _gzip_rotator
    file_handler.namer = _gzip_namer
    daily = TimedRotatingFileHandler(
        str(Path(LOG_FILE).with_name("app-daily.log")),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    daily.setFormatter(formatter)
    daily.rotator = _gzip_rotator
    daily.namer = _gzip_namer
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(daily)
    logger.addHandler(console_handler)


def log_exception(exc: BaseException, context: str = "") -> None:
    """Zapiši izjemo s sledjo sklada na nivoju ERROR."""
    suffix = f" ({context})" if context else ""
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("Napaka%s: %s\n%s", suffix, exc, stack)


def install_excepthook() -> None:
    """Prestrezanje neulovljenih izjem — traceback samo v dnevnik."""

    def _hook(exc_type, exc, tb) -> None:
        logger.critical(
            "Neulovljena izjema: %s",
            exc,
            exc_info=(exc_type, exc, tb),
        )
        try:
            from app.core.errors import handle_error

            handle_error(exc or exc_type("napaka"), context="crash")
        except Exception:
            pass

    sys.excepthook = _hook
