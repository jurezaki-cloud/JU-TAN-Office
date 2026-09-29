"""Authoritative SQLite lifecycle — single shutdown path for exit / fresh / wipe.

All application exit paths and destructive-reset preparation must call
``shutdown_database()`` so WAL/SHM locks are released before filesystem deletes.
"""

from __future__ import annotations

from pathlib import Path

from app.core.logger import logger


def shutdown_database(*, database=None) -> None:
    """Checkpoint the WAL and close the pooled connections this process can close.

    Safe to call multiple times. It does not block later work: ``connect()`` /
    ``Database.initialize()`` reopen the database (e.g. after a Fresh reset).
    Callers deleting DB files must still verify them with ``delete_database_files``.
    """
    if database is None:
        from app.database.database import db as database

    try:
        database.shutdown()
    except Exception:
        logger.exception("Database shutdown failed")
        # Best-effort: still try dispose so handles are released on Windows.
        try:
            database.dispose()
        except Exception:
            logger.exception("Database dispose after failed shutdown also failed")


def database_files(db_path: Path | str) -> tuple[Path, Path, Path]:
    """Return (main, wal, shm) paths for a SQLite database file."""
    base = Path(db_path)
    return base, Path(str(base) + "-wal"), Path(str(base) + "-shm")


def database_files_present(db_path: Path | str) -> list[Path]:
    """Paths that still exist on disk (main / wal / shm)."""
    return [p for p in database_files(db_path) if p.exists()]


def delete_database_files(db_path: Path | str) -> list[Path]:
    """Delete wal → shm → main after connections must already be closed.

    Returns paths that still exist (empty list = success).
    """
    main, wal, shm = database_files(db_path)
    # Safe order: WAL/SHM first, then main DB.
    for path in (wal, shm, main):
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("Could not delete %s: %s", path, exc)
    # Also clear SQLite journal/temp siblings if present.
    base = Path(db_path)
    for extra in (
        Path(str(base) + "-journal"),
        Path(str(base) + ".jutan-delete"),
        Path(str(base) + "-wal.jutan-delete"),
        Path(str(base) + "-shm.jutan-delete"),
    ):
        if extra.exists():
            try:
                extra.unlink()
            except OSError:
                pass
    return database_files_present(db_path)
