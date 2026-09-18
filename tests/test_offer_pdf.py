import tempfile
import unittest
from pathlib import Path

from app.services.offer_pdf import generate_offer_pdf


class OfferPdfTests(unittest.TestCase):
    def test_pdf_is_generated(self):
        offer = (1, "P-2026-000001", 1, "2026-09-18", "2026-10-18",
                 "Osnutek", 20.00, 2.00, 3.96, 21.96, "Hvala & lep pozdrav", "")
        customer = (1, "Čebelica d.o.o.", "Ana", "Glavna 1", "1000",
                    "Ljubljana", "Slovenija", "SI123", "a@example.com", "")
        items = [(1, None, "S1", "Svetovanje", "", 2.0, "ura",
                  10.0, 10.0, 22.0, 21.96)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ponudba.pdf"
            generate_offer_pdf(
                path, offer, customer, items,
                {"company_name": "JU-TAN Test", "iban": "SI561234"},
            )
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 1000)
