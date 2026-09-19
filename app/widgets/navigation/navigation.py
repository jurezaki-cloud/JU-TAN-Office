"""Business-logic navigation groups and page indices."""

from __future__ import annotations

PAGE_INDEX = {
    "dashboard": 0,
    "invoices": 1,
    "customers": 2,
    "offers": 3,
    "articles": 4,
    "company": 5,
    "payments": 6,
    "analytics": 7,
    "settings": 8,
    "orders": 9,
    "warehouse": 10,
    "suppliers": 11,
    "purchase": 12,
    "documents": 13,
    "crm": 14,
    "reports": 15,
    "automation": 16,
    "travel_orders": 17,
}

# Grouped navigation in business-workflow order (not stack-creation order).
NAV_GROUPS: list[tuple[str, list[tuple[str, int]]]] = [
    (
        "PREGLED",
        [
            ("Nadzorna plošča", 0),
        ],
    ),
    (
        "PRODAJA",
        [
            ("Računi", 1),
            ("Ponudbe", 3),
            ("Naročila", 9),
            ("Stranke", 2),
        ],
    ),
    (
        "IZDELKI IN NABAVA",
        [
            ("Artikli", 4),
            ("Skladišče", 10),
            ("Dobavitelji", 11),
            ("Nabava", 12),
        ],
    ),
    (
        "FINANCE",
        [
            ("Plačila", 6),
            ("Analitika", 7),
            ("Poročila", 15),
        ],
    ),
    (
        "POSLOVANJE",
        [
            ("Dokumenti", 13),
            ("CRM", 14),
            ("Potni nalogi", 17),
            ("Avtomatizacija", 16),
        ],
    ),
    (
        "SISTEM",
        [
            ("Podjetje", 5),
            ("Nastavitve", 8),
        ],
    ),
]
