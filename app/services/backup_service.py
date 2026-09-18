import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from app.core.constants import BACKUP_DIR
from app.database.database import db
from app.database.settings_repository import settings_repository


class BackupService:
    def __init__(self, database=None, backup_dir=None, settings=None):
        self.db = database or db
        self.backup_dir = Path(backup_dir or BACKUP_DIR)
        self.settings = settings or settings_repository

    def create(self, label="manual"):
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = self.backup_dir / f"ju-tan-{label}-{timestamp}.db"
        source = self.db.connect()
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
            result = target.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise sqlite3.DatabaseError("Backup integrity check failed")
        finally:
            target.close()
            source.close()
        return destination

    def list_backups(self):
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        return sorted(self.backup_dir.glob("ju-tan-*.db"), reverse=True)

    def cleanup(self, retention_days):
        cutoff = datetime.now() - timedelta(days=int(retention_days))
        removed = []
        for path in self.list_backups():
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            if modified < cutoff:
                path.unlink()
                removed.append(path)
        return removed

    def create_automatic_if_due(self):
        settings = self.settings.get()
        if not settings["auto_backup"]:
            return None
        today_marker = date.today().strftime("%Y%m%d")
        already_created = any(
            f"automatic-{today_marker}" in path.name
            for path in self.list_backups()
        )
        if already_created:
            return None
        backup = self.create(f"automatic-{today_marker}")
        self.cleanup(settings["backup_retention_days"])
        return backup

    def restore(self, backup_path):
        source_path = Path(backup_path).resolve()
        if not source_path.is_file():
            raise FileNotFoundError("Izbrana varnostna kopija ne obstaja.")
        source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
        try:
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise sqlite3.DatabaseError("Varnostna kopija je poškodovana.")
            safety_backup = self.create("before-restore")
            target = self.db.connect()
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            source.close()
        return safety_backup


backup_service = BackupService()
