"""Fresh install reset — Administrator-only destructive maintenance.

ALWAYS uses verified backup before any destruction.
NEVER touch paths outside JU-TAN-managed DATA_DIR / DATABASE_PATH.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.constants import BACKUP_DIR, DATA_DIR, DATABASE_PATH
from app.core.db_guard import integrity_ok, verify_backup
from app.core.logger import logger
from app.core.permissions import audit, can, current_user, require
from app.core.passwords import verify_password
from app.core.session import session
from app.database.database import db
from app.database.user_repository import user_repository


FRESH_CONFIRM_TEXT = "FRESH"

# Application brand assets — never delete these during Fresh.
PRESERVED_BRAND_NAMES = frozenset(
    {
        "logo.png",
        "logo_light.png",
        "logo_dark.png",
        "app.ico",
        "app.png",
    }
)

# Managed state files under DATA_DIR that Fresh may remove.
MANAGED_STATE_FILES = (
    "settings.json",
    "warehouse.json",
    "audit.jsonl",
    "session.json",
    "crash.flag",
    "app_version.txt",
    "last_vacuum.txt",
    ".machine_key",
)

MANAGED_STATE_GLOBS = (
    "company_logo.*",
    "drafts/*",
)


class FreshResetError(Exception):
    """User-facing Fresh failure."""


class FreshResetService:
    """Centralized production Fresh reset — Settings UI must not embed DELETE SQL."""

    def __init__(self, data_dir: Path | None = None, backup_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir or DATA_DIR)
        self.backup_dir = Path(backup_dir or BACKUP_DIR)
        self.database_path = Path(DATABASE_PATH)

    def assert_authorized(self) -> None:
        require("fresh")
        if not can("users"):
            raise PermissionError("Ponastavitev FRESH zahteva skrbniške pravice.")

    def verify_admin_password(self, password: str) -> None:
        """Re-authenticate the *current* administrator — unlocked session is not enough."""
        self.assert_authorized()
        user_id = session.user_id
        if user_id is None:
            # Fallback: look up by session username
            row = user_repository.get_by_username(session.user)
        else:
            row = user_repository.get_by_id(user_id)
        if row is None or not row.get("is_active"):
            raise PermissionError("Ponovna prijava ni uspela.")
        if row.get("role") != "Administrator" and "fresh" not in set(
            user_repository.get_permissions(row["id"])
        ):
            raise PermissionError("Ponastavitev FRESH zahteva skrbniške pravice.")
        if not verify_password(password or "", row["password_hash"]):
            raise PermissionError("Geslo ni pravilno.")

    def create_backup(self) -> Path:
        """Timestamped backup folder with SQLite (safe backup API) + managed state."""
        self.assert_authorized()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = self.backup_dir / "FreshReset" / f"JU-TAN-before-fresh-{stamp}"
        target.mkdir(parents=True, exist_ok=False)

        # 1) SQLite via backup API (consistent snapshot)
        db_target = target / "ju_tan.db"
        self._sqlite_backup(self.database_path, db_target)
        if not verify_backup(db_target):
            shutil.rmtree(target, ignore_errors=True)
            raise FreshResetError(
                "Varnostna kopija baze ni prestala preverjanja. Ponastavitev je prekinjena."
            )

        # 2) settings.json
        settings_src = self.data_dir / "settings.json"
        if settings_src.is_file():
            shutil.copy2(settings_src, target / "settings.json")

        # 3) warehouse.json
        wh = self.data_dir / "warehouse.json"
        if wh.is_file():
            shutil.copy2(wh, target / "warehouse.json")

        # 4) company logos inside DATA_DIR
        for path in self.data_dir.glob("company_logo.*"):
            if path.is_file():
                shutil.copy2(path, target / path.name)

        # 5) managed documents directory
        docs = self.data_dir / "documents"
        if docs.is_dir():
            shutil.copytree(docs, target / "documents", dirs_exist_ok=True)

        # 6) audit trail
        audit_file = self.data_dir / "audit.jsonl"
        if audit_file.is_file():
            shutil.copy2(audit_file, target / "audit.jsonl")

        # 7) manifest for future restore compatibility
        manifest = {
            "created_at": stamp,
            "kind": "fresh-pre-reset",
            "database": "ju_tan.db",
            "data_dir": str(self.data_dir),
            "user": current_user(),
        }
        (target / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        if not self.verify_backup_folder(target):
            raise FreshResetError(
                "Varnostna kopija ni celovita. Ponastavitev je prekinjena."
            )
        audit("fresh", f"backup:{target}")
        return target

    def verify_backup_folder(self, folder: Path) -> bool:
        db_path = Path(folder) / "ju_tan.db"
        return db_path.is_file() and verify_backup(db_path)

    def execute(
        self,
        *,
        password: str,
        confirm_text: str,
    ) -> Path:
        """Full Fresh pipeline. Returns backup path. Raises on any pre-delete failure."""
        self.assert_authorized()
        if (confirm_text or "").strip() != FRESH_CONFIRM_TEXT:
            raise FreshResetError("Za potrditev vnesite natančno besedo FRESH.")
        self.verify_admin_password(password)

        backup_path = self.create_backup()
        if not self.verify_backup_folder(backup_path):
            raise FreshResetError(
                "Varnostna kopija ni prestala preverjanja. Podatki niso bili izbrisani."
            )

        try:
            self._destructive_reset()
        except Exception as exc:
            logger.exception("Fresh reset failed after backup at %s", backup_path)
            raise FreshResetError(
                "Ponastavitev ni uspela. Varnostna kopija je ohranjena na: "
                f"{backup_path}"
            ) from exc

        if not integrity_ok(self.database_path):
            raise FreshResetError(
                "Baza po ponastavitvi ni konsistentna. "
                f"Varnostna kopija: {backup_path}"
            )

        audit("fresh", f"completed:{backup_path}")
        return backup_path

    def _destructive_reset(self) -> None:
        # Dispose pooled connections before replacing the file.
        db.dispose()

        # Remove DB (+ WAL/SHM)
        for suffix in ("", "-wal", "-shm"):
            path = Path(str(self.database_path) + suffix)
            if path.exists():
                path.unlink()

        # Recreate canonical schema via official bootstrap
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        db.initialize()
        user_repository.ensure_schema()
        # Ensure users table empty (initialize does not seed users)
        user_repository.delete_all_users()

        # Reset managed settings to defaults (setup_complete=False, no credentials)
        self._reset_settings()

        # Clear managed business files (never brand logos, never outside DATA_DIR)
        self._reset_managed_files()

        # Clear session / RBAC
        session.clear()

    def _reset_settings(self) -> None:
        from app.core.config_guard import stamp
        from app.modules.settings.settings_controller import default_settings

        settings_path = self.data_dir / "settings.json"
        fresh = default_settings()
        fresh["setup_complete"] = False
        fresh["password_hash"] = ""
        fresh["administrator"] = ""
        fresh["remember_user"] = False
        fresh["role"] = "Administrator"
        fresh["account_enabled"] = True
        fresh["legacy_auth_migrated"] = False
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(stamp(fresh), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _reset_managed_files(self) -> None:
        from app.core.security import ensure_inside

        root = self.data_dir.resolve()

        for name in MANAGED_STATE_FILES:
            if name in PRESERVED_BRAND_NAMES:
                continue
            path = ensure_inside(root / name, root)
            if path.is_file():
                # settings.json already rewritten
                if path.name == "settings.json":
                    continue
                path.unlink(missing_ok=True)

        for pattern in ("company_logo.*",):
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                if path.name in PRESERVED_BRAND_NAMES:
                    continue
                ensure_inside(path, root).unlink(missing_ok=True)

        drafts = ensure_inside(root / "drafts", root)
        if drafts.is_dir():
            shutil.rmtree(drafts, ignore_errors=True)

        documents = ensure_inside(root / "documents", root)
        if documents.is_dir():
            shutil.rmtree(documents, ignore_errors=True)
            documents.mkdir(parents=True, exist_ok=True)

        # Explicitly do NOT delete:
        # - logo.png / logo_light.png / logo_dark.png (JU-TAN branding)
        # - anything outside DATA_DIR
        # - Backup/ folder (contains the pre-fresh backup)
        # - user Desktop/Documents/Downloads / pdf.folder exports

    @staticmethod
    def _sqlite_backup(source: Path, dest: Path) -> None:
        if not source.exists():
            # Empty DB — create empty destination via initialize path later;
            # still write an empty valid sqlite file for backup completeness.
            conn = sqlite3.connect(dest)
            conn.close()
            return
        src = sqlite3.connect(str(source))
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()


fresh_reset_service = FreshResetService()
