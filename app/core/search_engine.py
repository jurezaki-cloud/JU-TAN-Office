"""Indeksirano iskanje z TTL predpomnilnikom in opcijskim FTS5."""

from __future__ import annotations

import re
import sqlite3

from app.core.cache import ttl_cache
from app.core.pagination import GRID_PAGE_SIZE
from app.database.database import db

_FTS_READY = False


def fts_query(text: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_čšžČŠŽ]+", text or "")
    if not tokens:
        return ""
    return " AND ".join(f"{token}*" for token in tokens[:8])


def ensure_search_schema(conn: sqlite3.Connection | None = None) -> bool:
    global _FTS_READY
    own = conn is None
    if own:
        conn = db.connect()
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(code, name)")
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS customers_fts USING fts5(company, contact, city)"
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS articles_fts_ai AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, code, name) VALUES (new.id, new.code, new.name);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS articles_fts_ad AFTER DELETE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS articles_fts_au AFTER UPDATE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
                INSERT INTO articles_fts(rowid, code, name) VALUES (new.id, new.code, new.name);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS customers_fts_ai AFTER INSERT ON customers BEGIN
                INSERT INTO customers_fts(rowid, company, contact, city)
                VALUES (new.id, new.company, new.contact, new.city);
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS customers_fts_ad AFTER DELETE ON customers BEGIN
                DELETE FROM customers_fts WHERE rowid = old.id;
            END
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS customers_fts_au AFTER UPDATE ON customers BEGIN
                DELETE FROM customers_fts WHERE rowid = old.id;
                INSERT INTO customers_fts(rowid, company, contact, city)
                VALUES (new.id, new.company, new.contact, new.city);
            END
            """
        )
        if conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO articles_fts(rowid, code, name) SELECT id, code, name FROM articles"
            )
        if conn.execute("SELECT COUNT(*) FROM customers_fts").fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO customers_fts(rowid, company, contact, city) "
                "SELECT id, company, contact, city FROM customers"
            )
        if own:
            conn.commit()
        _FTS_READY = True
        return True
    except sqlite3.OperationalError:
        _FTS_READY = False
        return False
    finally:
        if own:
            conn.close()


def fts_available() -> bool:
    return _FTS_READY


@ttl_cache(seconds=2.0)
def cached_article_page(text: str, limit: int = GRID_PAGE_SIZE, offset: int = 0):
    from app.database.article_repository import article_repository

    return article_repository.list_page(text, limit=limit, offset=offset)


@ttl_cache(seconds=2.0)
def cached_customer_page(text: str, limit: int = GRID_PAGE_SIZE, offset: int = 0):
    from app.database.customer_repository import customer_repository

    return customer_repository.list_page(text, limit=limit, offset=offset)


def invalidate_search_cache() -> None:
    cached_article_page.cache_clear()
    cached_customer_page.cache_clear()
