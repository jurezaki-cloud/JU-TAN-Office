import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(
            Path(self.temp_directory.name) / "ju_tan_test.db"
        )
        self.database.initialize()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_initialize_creates_expected_tables(self):
        with self.database.connect() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        self.assertTrue(
            {"customers", "articles", "offers", "offer_items"} <= tables
        )

    def test_foreign_keys_are_enabled(self):
        with self.database.connect() as connection:
            enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]

        self.assertEqual(enabled, 1)

    def test_offer_requires_existing_customer(self):
        with self.database.connect() as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO offers(number, customer_id, issue_date)
                    VALUES (?, ?, ?)
                    """,
                    ("P-TEST-000001", 999, "2026-09-18"),
                )

    def test_transaction_rolls_back_after_error(self):
        with self.assertRaises(RuntimeError):
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO articles(code, name) VALUES (?, ?)",
                    ("ROLLBACK", "Ne sme ostati"),
                )
                raise RuntimeError("test")

        with self.database.connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM articles WHERE code=?", ("ROLLBACK",)
            ).fetchone()[0]

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
