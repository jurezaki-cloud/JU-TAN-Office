import sqlite3
import unittest

from app.core.errors import friendly_error_message


class ErrorMessageTests(unittest.TestCase):
    def test_validation_message_is_preserved(self):
        self.assertEqual(
            friendly_error_message(ValueError("Podjetje je obvezno.")),
            "Podjetje je obvezno.",
        )

    def test_database_details_are_not_exposed(self):
        message = friendly_error_message(sqlite3.OperationalError("disk I/O"))
        self.assertNotIn("disk I/O", message)

    def test_duplicate_has_clear_message(self):
        message = friendly_error_message(
            sqlite3.IntegrityError("UNIQUE constraint failed: articles.code")
        )
        self.assertIn("že obstaja", message)
