"""Global search must never leak a forbidden page or mutate records."""
import sqlite3

from app.services import global_search


class Connection:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, *args):
        return self.raw.execute(*args)

    def close(self):
        pass


def test_search_permissions_and_literal_wildcards(monkeypatch):
    raw = sqlite3.connect(":memory:")
    raw.execute("CREATE TABLE customers (id INTEGER, company TEXT, contact TEXT, email TEXT, tax_number TEXT)")
    raw.execute("INSERT INTO customers VALUES (1, 'Novak_100%', NULL, NULL, NULL)")
    raw.execute("INSERT INTO customers VALUES (2, 'NovakX100Y', NULL, NULL, NULL)")
    monkeypatch.setattr(global_search.db, "connect", lambda: Connection(raw))
    monkeypatch.setattr(global_search, "can_open_page", lambda page: page == 2)
    hits = global_search.search_records("Novak_100%")
    assert [hit.record_id for hit in hits] == [1]
    assert global_search.search_records("No")[0].page == 2
    monkeypatch.setattr(global_search, "can_open_page", lambda page: False)
    assert global_search.search_records("Novak") == []
    assert raw.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 2
    raw.close()
