"""Versioned SQLite schema migrations (idempotent steps)."""

from __future__ import annotations

import sqlite3

from app.core.logger import logger

# Document branding defaults (ERP navy + JU-TAN green).
DEFAULT_PRIMARY = "#0F172A"
DEFAULT_ACCENT = "#059669"
DEFAULT_TABLE_HEADER = "#F1F5F9"

_BRANDING_COLUMNS = {
    "signature_path": "TEXT",
    "stamp_path": "TEXT",
    "doc_primary_color": f"TEXT DEFAULT '{DEFAULT_PRIMARY}'",
    "doc_accent_color": f"TEXT DEFAULT '{DEFAULT_ACCENT}'",
    "doc_table_header_color": f"TEXT DEFAULT '{DEFAULT_TABLE_HEADER}'",
}


def migrate_company_branding(conn: sqlite3.Connection) -> None:
    """
    Schema v3: company document branding columns + seed defaults.

    Idempotent — safe on fresh CREATE TABLE (columns already present) and
    on legacy databases that only have the pre-branding company shape.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
    )
    if not cursor.fetchone():
        return

    cols = {
        row[1] for row in cursor.execute("PRAGMA table_info(company)").fetchall()
    }
    for name, ddl in _BRANDING_COLUMNS.items():
        if name not in cols:
            cursor.execute(f"ALTER TABLE company ADD COLUMN {name} {ddl}")

    cursor.execute(
        """
        UPDATE company SET
            doc_primary_color=COALESCE(NULLIF(doc_primary_color, ''), ?),
            doc_accent_color=COALESCE(NULLIF(doc_accent_color, ''), ?),
            doc_table_header_color=COALESCE(NULLIF(doc_table_header_color, ''), ?)
        WHERE id = 1
        """,
        (DEFAULT_PRIMARY, DEFAULT_ACCENT, DEFAULT_TABLE_HEADER),
    )

    # One-time: copy legacy settings.json signature/stamp into empty DB columns.
    try:
        from app.modules.settings.settings_controller import SettingsController

        pdf = SettingsController().load_extras().get("pdf") or {}
        sig = str(pdf.get("signature_path") or "").strip()
        stamp = str(pdf.get("stamp_path") or "").strip()
        if sig:
            cursor.execute(
                """
                UPDATE company SET signature_path=?
                WHERE id = 1 AND (signature_path IS NULL OR signature_path = '')
                """,
                (sig,),
            )
        if stamp:
            cursor.execute(
                """
                UPDATE company SET stamp_path=?
                WHERE id = 1 AND (stamp_path IS NULL OR stamp_path = '')
                """,
                (stamp,),
            )
    except Exception:
        logger.debug("Legacy PDF path seed skipped.", exc_info=True)


def apply_pending_migrations(from_version: int, to_version: int, conn: sqlite3.Connection) -> None:
    """Run migration steps for versions in (from_version, to_version]."""
    if from_version < 3 <= to_version:
        migrate_company_branding(conn)
        logger.info("Applied schema migration → 3 (company branding).")
