import pytest

from app.modules.customers.services.company_lookup import CompanyLookupError, normalize_tax_number


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12345678", "12345678"),
        ("SI12345678", "12345678"),
        ("si 12345678", "12345678"),
    ],
)
def test_normalize_tax_number(raw, expected):
    assert normalize_tax_number(raw) == expected


@pytest.mark.parametrize("raw", ["", "123", "SI1234567", "abcdefgh", "123456789"])
def test_invalid_tax_number(raw):
    with pytest.raises(CompanyLookupError):
        normalize_tax_number(raw)
