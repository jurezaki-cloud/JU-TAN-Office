import tempfile
import unittest
from pathlib import Path

from app.database.database import Database
from app.services.numbering_service import NumberingService


class NumberingTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_directory.name) / "test.db")
        self.database.initialize()
        self.numbering = NumberingService(self.database)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_offer_numbers_are_sequential_per_year(self):
        self.assertEqual(
            self.numbering.preview_offer_number(2026), "P-2026-000001"
        )
        self.assertEqual(self.numbering.next_offer_number(2026), "P-2026-000001")
        self.assertEqual(self.numbering.next_offer_number(2026), "P-2026-000002")
        self.assertEqual(self.numbering.next_offer_number(2027), "P-2027-000001")
