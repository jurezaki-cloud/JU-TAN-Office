import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.database.database import Database
from app.database.settings_repository import SettingsRepository
from app.services.backup_service import BackupService


class SettingsBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        root = Path(self.temp_directory.name)
        self.database = Database(root / "data" / "test.db")
        self.database.initialize()
        self.settings = SettingsRepository(self.database)
        self.backups = BackupService(
            self.database, root / "backups", self.settings
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_company_settings_are_validated_and_saved(self):
        values = self.settings.get()
        values.update({
            "company_name": "JU-TAN Test", "email": "INFO@EXAMPLE.COM",
            "iban": "SI56 1234", "payment_terms_days": 30,
        })
        saved = self.settings.update(values)
        self.assertEqual(saved["company_name"], "JU-TAN Test")
        self.assertEqual(saved["email"], "info@example.com")
        self.assertEqual(saved["iban"], "SI561234")
        self.assertEqual(saved["payment_terms_days"], 30)

    def test_backup_and_restore_preserve_data(self):
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO articles(code, name) VALUES('B1', 'Pred kopijo')"
            )
        backup = self.backups.create()
        with self.database.transaction() as connection:
            connection.execute("DELETE FROM articles")
        safety = self.backups.restore(backup)
        with self.database.connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        self.assertEqual(count, 1)
        self.assertTrue(safety.exists())

    def test_automatic_backup_runs_only_once_per_day(self):
        first = self.backups.create_automatic_if_due()
        second = self.backups.create_automatic_if_due()
        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_cleanup_removes_only_expired_backups(self):
        old_backup = self.backups.create("old")
        current_backup = self.backups.create("current")
        old_time = (datetime.now() - timedelta(days=40)).timestamp()
        os.utime(old_backup, (old_time, old_time))
        removed = self.backups.cleanup(30)
        self.assertIn(old_backup, removed)
        self.assertTrue(current_backup.exists())
