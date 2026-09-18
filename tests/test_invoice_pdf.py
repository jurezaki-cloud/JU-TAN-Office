import tempfile
import unittest
from pathlib import Path

from app.services.invoice_pdf import generate_invoice_pdf
from app.services.document_pdf import sepa_payload


class InvoicePdfTests(unittest.TestCase):
    def test_invoice_pdf_is_generated(self):
        invoice = (1, "R-2026-000001", 1, 1, "2026-09-18", "2026-10-03",
                   "Delno plačan", 20.0, 2.0, 3.96, 21.96, 10.0, "", "")
        customer = (1, "Čebelica d.o.o.", "Ana", "Glavna 1", "1000",
                    "Ljubljana", "Slovenija", "SI123", "a@example.com", "")
        items = [(1, None, "S1", "Storitev", "", 2.0, "ura",
                  10.0, 10.0, 22.0, 21.96)]
        payments = [(1, "2026-09-20", 10.0, "Nakazilo", "SI00", "")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "racun.pdf"
            generate_invoice_pdf(
                path, invoice, customer, items, payments,
                {"company_name": "JU-TAN Test", "iban": "SI561234"},
            )
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 1000)

    def test_sepa_qr_contains_payment_data(self):
        payload = sepa_payload(
            {"company_name": "JU-TAN Test", "iban": "SI56 1234"},
            21.96,
            "R-2026-000001",
        )
        self.assertIn("SI561234", payload)
        self.assertIn("EUR21.96", payload)
        self.assertIn("R-2026-000001", payload)

    def test_sepa_qr_requires_iban(self):
        self.assertIsNone(sepa_payload({"company_name": "JU-TAN"}, 10, "R-1"))
