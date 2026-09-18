import tempfile
import unittest
from pathlib import Path

from app.database.database import Database
from app.database.invoice_repository import InvoiceRepository
from app.database.offer_repository import OfferRepository
from app.database.repository import CustomerRepository


class InvoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_directory.name) / "test.db")
        self.database.initialize()
        self.customers = CustomerRepository(self.database)
        self.offers = OfferRepository(self.database)
        self.invoices = InvoiceRepository(self.database)
        customer_id = self.customers.add(
            "Kupec", "", "", "", "", "", "", "", "",
        )
        self.offer_id = self.offers.create_with_items(
            "P-2026-000001", customer_id, "2026-09-18", "2026-10-18",
            "Sprejeta", "", [{
                "article_id": None, "code": "S1", "name": "Storitev",
                "description": "", "quantity": 2, "unit": "ura",
                "price": 10, "discount": 10, "vat": 22,
            }],
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_offer_is_converted_once_with_items(self):
        invoice_id = self.invoices.create_from_offer(
            self.offer_id, "2026-09-18", "2026-10-03"
        )
        invoice = self.invoices.get_by_id(invoice_id)
        self.assertEqual(invoice[1], "R-2026-000001")
        self.assertEqual(invoice[10], 21.96)
        self.assertEqual(len(self.invoices.get_items(invoice_id)), 1)
        with self.assertRaises(ValueError):
            self.invoices.create_from_offer(
                self.offer_id, "2026-09-18", "2026-10-03"
            )

    def test_partial_and_full_payment_update_status(self):
        invoice_id = self.invoices.create_from_offer(
            self.offer_id, "2026-09-18", "2026-10-03"
        )
        self.invoices.add_payment(invoice_id, "2026-09-20", 10)
        invoice = self.invoices.get_by_id(invoice_id)
        self.assertEqual(invoice[6], "Delno plačan")
        self.assertEqual(invoice[11], 10.0)
        self.assertEqual(len(self.invoices.get_all_payments()), 1)
        self.invoices.add_payment(invoice_id, "2026-09-21", 11.96)
        invoice = self.invoices.get_by_id(invoice_id)
        self.assertEqual(invoice[6], "Plačan")
        self.assertEqual(invoice[11], 21.96)

    def test_source_offer_cannot_be_deleted_after_conversion(self):
        self.invoices.create_from_offer(
            self.offer_id, "2026-09-18", "2026-10-03"
        )
        with self.assertRaises(ValueError):
            self.offers.delete(self.offer_id)

    def test_overpayment_is_rejected(self):
        invoice_id = self.invoices.create_from_offer(
            self.offer_id, "2026-09-18", "2026-10-03"
        )
        with self.assertRaises(ValueError):
            self.invoices.add_payment(invoice_id, "2026-09-20", 30)

    def test_unaccepted_offer_cannot_be_invoiced(self):
        offer = self.offers.get_by_id(self.offer_id)
        self.offers.update_with_items(
            self.offer_id, offer[2], offer[3], offer[4], "Osnutek", offer[10],
            [{
                "article_id": None, "code": "S1", "name": "Storitev",
                "description": "", "quantity": 2, "unit": "ura",
                "price": 10, "discount": 10, "vat": 22,
            }],
        )
        with self.assertRaises(ValueError):
            self.invoices.create_from_offer(
                self.offer_id, "2026-09-18", "2026-10-03"
            )
