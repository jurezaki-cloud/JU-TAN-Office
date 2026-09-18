import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database.article_repository import ArticleRepository
from app.database.database import Database
from app.database.repository import CustomerRepository
from app.database.offer_repository import OfferRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_directory.name) / "test.db")
        self.database.initialize()
        self.customers = CustomerRepository(self.database)
        self.articles = ArticleRepository(self.database)
        self.offers = OfferRepository(self.database)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_customer_is_normalized_and_returned(self):
        customer_id = self.customers.add(
            "  Test d.o.o.  ", " Ana ", "", "1000", "Ljubljana",
            "Slovenija", "SI123", " ANA@EXAMPLE.COM ", "+386 1 234",
        )
        customer = self.customers.get_by_id(customer_id)

        self.assertEqual(customer[1], "Test d.o.o.")
        self.assertEqual(customer[8], "ana@example.com")

    def test_invalid_customer_email_is_rejected(self):
        with self.assertRaises(ValueError):
            self.customers.add(
                "Test", "", "", "", "", "", "", "ni-email", "",
            )

    def test_article_money_is_rounded_to_two_decimals(self):
        article_id = self.articles.add(
            "art0001", "Storitev", "", "ura", "10.005", "22",
        )
        article = self.articles.get_by_id(article_id)

        self.assertEqual(article[1], "ART0001")
        self.assertEqual(article[5], 10.01)

    def test_duplicate_article_code_is_rejected(self):
        self.articles.add("ART0001", "Prvi", "", "kos", 1, 22)
        with self.assertRaises(sqlite3.IntegrityError):
            self.articles.add("art0001", "Drugi", "", "kos", 2, 22)

    def test_offer_and_items_are_saved_transactionally(self):
        customer_id = self.customers.add(
            "Kupec", "", "", "", "", "", "", "", "",
        )
        offer_id = self.offers.create(
            "P-2026-000001", customer_id, "2026-09-18", "2026-10-18",
            "Osnutek", "10", "0", "2.20", "12.20", "",
        )
        self.offers.add_item(
            offer_id, None, "S001", "Storitev", "", "1.125", "ura",
            "10", "0", "22", "13.73",
        )

        self.assertEqual(len(self.offers.get_items(offer_id)), 1)
        self.offers.delete(offer_id)
        self.assertEqual(self.offers.get_items(offer_id), [])

    def test_complete_offer_recalculates_totals(self):
        customer_id = self.customers.add(
            "Kupec", "", "", "", "", "", "", "", "",
        )
        items = [{
            "article_id": None, "code": "S1", "name": "Storitev",
            "description": "", "quantity": 2, "unit": "ura", "price": 10,
            "discount": 10, "vat": 22,
        }]
        offer_id = self.offers.create_with_items(
            "P-2026-000002", customer_id, "2026-09-18", "2026-10-18",
            "Osnutek", "", items,
        )
        offer = self.offers.get_by_id(offer_id)
        self.assertEqual(offer[6:10], (20.0, 2.0, 3.96, 21.96))
