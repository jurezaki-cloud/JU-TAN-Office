"""Promised payments are separate from ledger payments and capped by balance."""
import sqlite3
from datetime import date

import pytest
from app.database import payment_promise_repository as module


class Connection:
    def __init__(self, raw):
        self.raw = raw
    def execute(self, *args):
        return self.raw.execute(*args)
    def commit(self):
        self.raw.commit()
    def close(self):
        pass


def test_promises_project_latest_open_balance(monkeypatch):
    raw = sqlite3.connect(":memory:")
    raw.executescript("""
        CREATE TABLE invoices(id INTEGER PRIMARY KEY, total REAL, status TEXT);
        CREATE TABLE payments(invoice_id INTEGER, amount REAL);
        INSERT INTO invoices VALUES(1, 1000, 'Izdan');
        INSERT INTO payments VALUES(1, 200);
    """)
    monkeypatch.setattr(module.db, "connect", lambda: Connection(raw))
    monkeypatch.setattr(module, "require", lambda action: None)
    repo = module.PaymentPromiseRepository()
    repo.record(1, "2026-10-01", 700, "prvi dogovor")
    repo.record(1, "2026-10-15", 600, "novi dogovor")
    assert repo.latest(1)[1] == 600
    assert repo.expected(date(2026, 9, 29)) == (0, 600)
    with pytest.raises(ValueError):
        repo.record(1, "2026-10-02", 801)
    assert raw.execute("SELECT SUM(amount) FROM payments").fetchone()[0] == 200
    raw.close()
