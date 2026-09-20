"""Zmogljivost: indeksi, paginacija, iskanje, nabor povezav, izvoz."""

import time

from app.core.cache import ttl_cache
from app.core.pagination import IncrementalLoader, GRID_PAGE_SIZE, page_slice
from app.core.search_engine import cached_article_page, fts_query, invalidate_search_cache
from app.core.thumbs import cleanup_temp
from app.database.article_repository import article_repository
from app.database.database import db


def test_page_slice_100k():
    rows = list(range(100_000))
    started = time.perf_counter()
    chunk = page_slice(rows, 0, 200)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert chunk == list(range(200))
    assert elapsed_ms < 50


def test_incremental_loader():
    data = list(range(1000))

    def fetch(offset, size):
        return data[offset:offset + size]

    loader = IncrementalLoader(fetch, page_size=200)
    first = loader.first()
    assert len(first) == 200
    more = loader.more()
    assert more[0] == 200
    while not loader.exhausted:
        loader.more()
    assert loader.offset == 1000


def test_search_cache_and_list_page():
    article_repository.add("PERF1", "Perf Artikel", "", "kos", 1, 22)
    invalidate_search_cache()
    rows = cached_article_page("Perf", limit=50, offset=0)
    started = time.perf_counter()
    again = cached_article_page("Perf", limit=50, offset=0)
    cached_ms = (time.perf_counter() - started) * 1000
    assert rows
    assert again == rows
    assert cached_ms < 20
    paged = article_repository.list_page("", limit=5, offset=0)
    assert len(paged) <= 5


def test_fts_query_tokens():
    assert "Office*" in fts_query("JU-TAN Office")
    assert fts_query("") == ""


def test_index_query_plan():
    conn = db.connect()
    plan = " ".join(
        " ".join(str(part) for part in row)
        for row in conn.execute(
            "EXPLAIN QUERY PLAN SELECT name FROM articles WHERE name = ?",
            ("x",),
        )
    ).lower()
    conn.close()
    assert "idx_articles_name" in plan or "index" in plan


def test_connection_pool_same_thread():
    a = db.connect()
    b = db.connect()
    raw_a = object.__getattribute__(a, "_raw")
    raw_b = object.__getattribute__(b, "_raw")
    assert raw_a is raw_b
    a.close()
    c = db.connect()
    assert object.__getattribute__(c, "_raw") is raw_a


def test_grid_page_size():
    assert GRID_PAGE_SIZE == 200


def test_temp_cleanup(tmp_path, monkeypatch):
    from app.core import thumbs

    monkeypatch.setattr(thumbs, "TEMP_DIR", tmp_path)
    stale = tmp_path / "old.tmp"
    stale.write_text("x")
    import os
    os.utime(stale, (0, 0))
    assert cleanup_temp(max_age=1) >= 1
    assert not stale.exists()


def test_excel_stream(tmp_path):
    from app.excel.excel_export import write_workbook_stream

    path = tmp_path / "big.xlsx"
    rows = [[i, f"n{i}"] for i in range(50)]
    write_workbook_stream(path, "products", ["A", "B"], rows)
    assert path.exists()
    assert path.stat().st_size > 0


def test_perf_snapshot():
    from app.core.perf import snapshot

    data = snapshot()
    assert "memory_mb" in data
    assert data["gc_objects"] > 0


def test_ttl_cache_speed():
    calls = {"n": 0}

    @ttl_cache(seconds=30)
    def heavy(n):
        calls["n"] += 1
        return sum(range(n))

    assert heavy(10_000) == heavy(10_000)
    assert calls["n"] == 1
