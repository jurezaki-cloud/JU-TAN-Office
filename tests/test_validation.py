import unittest
from decimal import Decimal

from app.core.validation import calculate_line_total, decimal_value


class ValidationTests(unittest.TestCase):
    def test_line_total_uses_decimal_rounding(self):
        total = calculate_line_total("3", "19.99", "10", "22")
        self.assertEqual(total, Decimal("65.85"))

    def test_negative_money_is_rejected(self):
        with self.assertRaises(ValueError):
            decimal_value("-0.01", "Cena")
