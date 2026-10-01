"""Assistant queries use real balances and avoid writes."""
import sqlite3
from datetime import date

from app.services import business_assistant as assistant


class Connection:
    def __init__(self, raw):
        self.raw = raw
    def execute(self, *args):
        return self.raw.execute(*args)
    def close(self):
        pass


def test_debtors_exclude_drafts_and_subtract_partial_payments(monkeypatch):
    raw = sqlite3.connect(":memory:")
    raw.executescript("""
        CREATE TABLE customers(id INTEGER, company TEXT);
        CREATE TABLE invoices(id INTEGER, customer_id INTEGER, total REAL, status TEXT,
                              issue_date TEXT);
        CREATE TABLE payments(invoice_id INTEGER, amount REAL);
        INSERT INTO customers VALUES(1, 'Novak'), (2, 'Kovacevic');
        INSERT INTO invoices VALUES(1, 1, 700, 'Delno plačan', '2026-09-01');
        INSERT INTO invoices VALUES(2, 1, 999, 'Osnutek', '2026-09-02');
        INSERT INTO invoices VALUES(3, 2, 600, 'Izdan', '2026-09-03');
        INSERT INTO payments VALUES(1, 300);
    """)
    monkeypatch.setattr(assistant, "can_open_page", lambda page: True)
    from app.database import database
    monkeypatch.setattr(database.db, "connect", lambda: Connection(raw))
    result = assistant.answer("Kdo mi dolguje več kot 500 €?")
    assert "Kovacevic" in result.body
    assert "Novak" not in result.body
    monkeypatch.setattr(assistant, "can_open_page", lambda page: page != 2)
    assert "Kovacevic" not in assistant.answer("Kdo mi dolguje več kot 500 €?").body
    raw.close()


def test_waiting_offers_are_sent_and_old(monkeypatch):
    raw = sqlite3.connect(":memory:")
    raw.executescript("""
        CREATE TABLE customers(id INTEGER, company TEXT);
        CREATE TABLE offers(number TEXT, customer_id INTEGER, issue_date TEXT, status TEXT);
        INSERT INTO customers VALUES(1, 'Stranka');
        INSERT INTO offers VALUES('P-1', 1, '2026-09-01', 'Poslana');
        INSERT INTO offers VALUES('P-2', 1, '2026-09-20', 'Poslana');
        INSERT INTO offers VALUES('P-3', 1, '2026-09-01', 'Sprejeta');
    """)
    from app.database import database
    monkeypatch.setattr(database.db, "connect", lambda: Connection(raw))
    monkeypatch.setattr(assistant, "can_open_page", lambda page: True)
    result = assistant.answer("Pokaži ponudbe, ki čakajo več kot 14 dni", date(2026, 9, 29))
    assert "P-1" in result.body and "P-2" not in result.body and "P-3" not in result.body
    raw.close()


def test_low_stock_phrase_uses_warehouse_service(monkeypatch):
    from types import SimpleNamespace
    from app.modules.warehouse import warehouse_service
    monkeypatch.setattr(assistant, "can_open_page", lambda page: page == 10)
    monkeypatch.setattr(warehouse_service.WarehouseService, "stock_rows", lambda self: [
        SimpleNamespace(name="Papir", warehouse="Glavno", free=2,
                        min_qty=5),
        SimpleNamespace(name="Toner", warehouse="Glavno", free=10,
                        min_qty=5),
    ])
    result = assistant.answer("Kateri artikli imajo nizko zalogo?")
    assert "Papir" in result.body and "Toner" not in result.body
