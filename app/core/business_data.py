"""Business-record inventory — system scaffold vs user business data.

Fresh production databases may contain:
- schema / tables
- empty singleton ``company`` row (id=1, blank name) for first-run save
- reference defaults (VAT rates in schema defaults, branding color defaults)

They must NOT contain named companies, customers, articles, documents, etc.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# Tables that hold user business records (not system-only).
BUSINESS_TABLES: tuple[str, ...] = (
    "customers",
    "articles",
    "invoices",
    "invoice_items",
    "offers",
    "offer_items",
    "orders",
    "order_items",
    "payments",
    "suppliers",
    "purchases",
    "purchase_items",
    "travel_orders",
    "documents",
    "users",
)


DEMO_NAME_NEEDLES: tuple[str, ...] = (
    "test d.o.o",
    "demo",
    "sample",
    "fixture",
    "acme",
)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _count(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def configured_company_count(conn: sqlite3.Connection) -> int:
    """Companies with a non-empty name (empty singleton scaffold = 0)."""
    if not _table_exists(conn, "company"):
        return 0
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM company "
            "WHERE TRIM(COALESCE(name, '')) <> ''"
        ).fetchone()[0]
    )


def business_record_counts(db_path: Path | str | None = None, *, conn: sqlite3.Connection | None = None) -> dict[str, int]:
    """Return counts of user business records for a database file or open connection."""
    own = False
    if conn is None:
        path = Path(db_path) if db_path else None
        if path is None or not path.exists():
            return {
                "companies": 0,
                "customers": 0,
                "articles": 0,
                "invoices": 0,
                "offers": 0,
                "orders": 0,
                "payments": 0,
                "suppliers": 0,
                "purchases": 0,
                "travel_orders": 0,
                "documents": 0,
                "users": 0,
                "invoice_items": 0,
                "offer_items": 0,
                "order_items": 0,
                "purchase_items": 0,
            }
        conn = sqlite3.connect(str(path))
        own = True
    try:
        counts = {
            "companies": configured_company_count(conn),
            "customers": _count(conn, "customers"),
            "articles": _count(conn, "articles"),
            "invoices": _count(conn, "invoices"),
            "offers": _count(conn, "offers"),
            "orders": _count(conn, "orders"),
            "payments": _count(conn, "payments"),
            "suppliers": _count(conn, "suppliers"),
            "purchases": _count(conn, "purchases"),
            "travel_orders": _count(conn, "travel_orders"),
            "documents": _count(conn, "documents"),
            "users": _count(conn, "users"),
            "invoice_items": _count(conn, "invoice_items"),
            "offer_items": _count(conn, "offer_items"),
            "order_items": _count(conn, "order_items"),
            "purchase_items": _count(conn, "purchase_items"),
        }
        return counts
    finally:
        if own:
            conn.close()


def is_business_empty(counts: dict[str, int] | None = None, **kwargs: Any) -> bool:
    data = counts if counts is not None else business_record_counts(**kwargs)
    return all(int(v) == 0 for v in data.values())


def find_demo_like_names(conn: sqlite3.Connection) -> list[str]:
    """Heuristic scan for demo/test company or customer names."""
    hits: list[str] = []
    if _table_exists(conn, "company"):
        for (name,) in conn.execute(
            "SELECT name FROM company WHERE TRIM(COALESCE(name,'')) <> ''"
        ):
            lowered = str(name or "").casefold()
            if any(n in lowered for n in DEMO_NAME_NEEDLES):
                hits.append(f"company:{name}")
    if _table_exists(conn, "customers"):
        for (name,) in conn.execute(
            "SELECT company FROM customers WHERE TRIM(COALESCE(company,'')) <> ''"
        ):
            lowered = str(name or "").casefold()
            if any(n in lowered for n in DEMO_NAME_NEEDLES):
                hits.append(f"customer:{name}")
    if _table_exists(conn, "articles"):
        for (name,) in conn.execute(
            "SELECT name FROM articles WHERE TRIM(COALESCE(name,'')) <> ''"
        ):
            lowered = str(name or "").casefold()
            if any(n in lowered for n in DEMO_NAME_NEEDLES):
                hits.append(f"article:{name}")
    return hits


def assert_fresh_production_database(db_path: Path | str) -> dict[str, int]:
    """Raise AssertionError if DB is not a clean production business environment."""
    path = Path(db_path)
    if not path.exists():
        raise AssertionError(f"Database missing: {path}")
    conn = sqlite3.connect(str(path))
    try:
        counts = business_record_counts(conn=conn)
        if not is_business_empty(counts):
            raise AssertionError(f"Business data present in fresh DB: {counts}")
        demos = find_demo_like_names(conn)
        if demos:
            raise AssertionError(f"Demo-like names in fresh DB: {demos}")
        return counts
    finally:
        conn.close()


__all__ = [
    "BUSINESS_TABLES",
    "assert_fresh_production_database",
    "business_record_counts",
    "configured_company_count",
    "find_demo_like_names",
    "is_business_empty",
]
