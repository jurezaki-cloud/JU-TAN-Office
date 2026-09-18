import unittest
from decimal import Decimal

from app.services.offer_calculation import calculate_offer


class OfferCalculationTests(unittest.TestCase):
    def test_multiple_items_have_exact_totals(self):
        result = calculate_offer([
            {"quantity": 2, "price": "10.00", "discount": 10, "vat": 22},
            {"quantity": 1, "price": "5.55", "discount": 0, "vat": 9.5},
        ])
        self.assertEqual(result["subtotal"], Decimal("25.55"))
        self.assertEqual(result["discount"], Decimal("2.00"))
        self.assertEqual(result["vat"], Decimal("4.49"))
        self.assertEqual(result["total"], Decimal("28.04"))

    def test_invalid_discount_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_offer([
                {"quantity": 1, "price": 10, "discount": 101, "vat": 22}
            ])
