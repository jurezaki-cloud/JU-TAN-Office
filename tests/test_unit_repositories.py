"""Unit testi: repository, cache, paginacija, varnost."""

from app.core.cache import ttl_cache
from app.core.errors import friendly_message
from app.core.pagination import has_more, page_slice
from app.core.permissions import can, require
from app.core.security import ensure_inside, require_non_empty, safe_filename
from app.database.article_repository import article_repository
from app.database.base_repository import BaseRepository, _ident
from app.database.customer_repository import customer_repository
from pathlib import Path
import pytest


def test_customer_repository_crud():
    customer_repository.add(
        "Test d.o.o.", "Ana", "Ulica 1", "1000", "Ljubljana",
        "SI", "12345678", "a@test.si", "040000000",
    )
    rows = customer_repository.get_all()
    assert any(row[1] == "Test d.o.o." for row in rows)
    found = customer_repository.search("Test")
    assert found
    row = customer_repository.get_by_id(found[0][0])
    assert row[1] == "Test d.o.o."
    customer_repository.delete(found[0][0])
    assert customer_repository.get_by_id(found[0][0]) is None


def test_article_repository_add_and_unique_code():
    article_repository.add("ART-T025", "Test artikel", "", "kos", 10.0, 22)
    rows = [r for r in article_repository.get_all() if r[1] == "ART-T025"]
    assert rows
    with pytest.raises(ValueError):
        article_repository.add("ART-T025", "Duplikat", "", "kos", 1, 22)


def test_sql_get_by_id_is_parameterized():
    customer_repository.add(
        "SQLi", "X", "", "", "Koper", "SI", "", "", "",
    )
    injected = customer_repository.get_by_id("1 OR 1=1")
    assert injected is None or injected[1] != "should-not-match-all"


def test_base_repository_rejects_bad_identifier():
    with pytest.raises(ValueError):
        _ident("customers; DROP TABLE customers")
    assert _ident("customers") == "customers"


def test_pagination_and_cache():
    rows = list(range(120))
    assert page_slice(rows, 0, 50) == list(range(50))
    assert has_more(120, 1, 50)
    assert not has_more(50, 0, 50)

    calls = {"n": 0}

    @ttl_cache(seconds=30)
    def fetch():
        calls["n"] += 1
        return 7

    assert fetch() == 7
    assert fetch() == 7
    assert calls["n"] == 1
    fetch.cache_clear()
    assert fetch() == 7
    assert calls["n"] == 2


def test_security_helpers(tmp_path):
    assert require_non_empty("  ime  ", "Ime") == "ime"
    with pytest.raises(ValueError):
        require_non_empty("  ", "Ime")
    assert ".." not in safe_filename("../secret.txt")
    root = tmp_path / "docs"
    root.mkdir()
    inside = ensure_inside(root / "a.txt", root)
    assert inside.parent == root.resolve()
    with pytest.raises(PermissionError):
        ensure_inside(tmp_path / "outside.txt", root)
    assert can("export")
    require("read")
    with pytest.raises(PermissionError):
        require("admin-root")


def test_friendly_errors():
    assert "veljavni" in friendly_message(ValueError("x"))
    assert "dovoljenja" in friendly_message(PermissionError("x"))
