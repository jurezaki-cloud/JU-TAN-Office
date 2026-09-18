import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.database.database import Database
from app.database.invoice_repository import InvoiceRepository
from app.database.offer_repository import OfferRepository
from app.database.repository import CustomerRepository
from app.services.analytics_service import AnalyticsService


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_directory.name) / "test.db")
        self.database.initialize()
        customers = CustomerRepository(self.database)
        offers = OfferRepository(self.database)
        invoices = InvoiceRepository(self.database)
        customer_id = customers.add(
            "Analitika d.o.o.", "", "", "", "", "", "", "", "",
        )
        offer_id = offers.create_with_items(
            "P-2026-000001", customer_id, "2026-01-01", "2026-01-15",
            "Sprejeta", "", [{
                "article_id": None, "code": "A", "name": "Analiza",
                "description": "", "quantity": 1, "unit": "kos",
                "price": 100, "discount": 0, "vat": 22,
            }],
        )
        self.invoice_id = invoices.create_from_offer(
            offer_id, "2026-01-01", "2026-01-15"
        )
        invoices.add_payment(self.invoice_id, "2026-02-01", 22)
        self.analytics = AnalyticsService(self.database)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_summary_uses_real_business_data(self):
        summary = self.analytics.summary(date(2026, 9, 18))
        self.assertEqual(summary["customers"], 1)
        self.assertEqual(summary["offers"], 1)
        self.assertEqual(summary["invoices"], 1)
        self.assertEqual(summary["revenue"], 22.0)
        self.assertEqual(summary["open_amount"], 100.0)
        self.assertEqual(summary["overdue_amount"], 100.0)
        self.assertEqual(summary["overdue_count"], 1)

    def test_monthly_revenue_includes_empty_months(self):
        rows = self.analytics.monthly_revenue(3, date(2026, 3, 10))
        self.assertEqual(rows, [
            ("2026-01", 0.0), ("2026-02", 22.0), ("2026-03", 0.0),
        ])

    def test_receivables_and_top_customers(self):
        receivables = self.analytics.receivables(date(2026, 9, 18))
        self.assertEqual(receivables[0][6], 100.0)
        self.assertEqual(receivables[0][7], "Zapadel")
        top = self.analytics.top_customers()
        self.assertEqual(top[0], ("Analitika d.o.o.", 1, 122.0, 22.0))
