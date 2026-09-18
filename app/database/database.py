import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.constants import DATABASE_PATH
from app.core.logger import logger


class Database:

    def __init__(self, database_path=None):
        self.database = Path(database_path or DATABASE_PATH)

    def connect(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.database, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def transaction(self, immediate=False):
        """Yield a connection and always commit or roll back safely."""
        conn = self.connect()
        try:
            if immediate:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    contact TEXT,
                    address TEXT,
                    postal_code TEXT,
                    city TEXT,
                    country TEXT,
                    tax_number TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    unit TEXT,
                    price REAL DEFAULT 0,
                    vat REAL DEFAULT 22,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL UNIQUE,
                    customer_id INTEGER NOT NULL,
                    issue_date TEXT NOT NULL,
                    valid_until TEXT,
                    status TEXT DEFAULT 'Osnutek',
                    subtotal REAL DEFAULT 0,
                    discount REAL DEFAULT 0,
                    vat REAL DEFAULT 0,
                    total REAL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(customer_id)
                        REFERENCES customers(id)
                        ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS offer_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    offer_id INTEGER NOT NULL,
                    article_id INTEGER,
                    code TEXT,
                    name TEXT,
                    description TEXT,
                    quantity REAL DEFAULT 1,
                    unit TEXT,
                    price REAL DEFAULT 0,
                    discount REAL DEFAULT 0,
                    vat REAL DEFAULT 22,
                    total REAL DEFAULT 0,
                    FOREIGN KEY(offer_id)
                        REFERENCES offers(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY(article_id)
                        REFERENCES articles(id)
                        ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS document_sequences (
                    document_type TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    last_number INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(document_type, year)
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL UNIQUE,
                    customer_id INTEGER NOT NULL,
                    source_offer_id INTEGER UNIQUE,
                    issue_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Neplačan',
                    subtotal REAL NOT NULL DEFAULT 0,
                    discount REAL NOT NULL DEFAULT 0,
                    vat REAL NOT NULL DEFAULT 0,
                    total REAL NOT NULL DEFAULT 0,
                    paid_amount REAL NOT NULL DEFAULT 0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                        ON DELETE RESTRICT,
                    FOREIGN KEY(source_offer_id) REFERENCES offers(id)
                        ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    article_id INTEGER,
                    code TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    quantity REAL NOT NULL DEFAULT 1,
                    unit TEXT,
                    price REAL NOT NULL DEFAULT 0,
                    discount REAL NOT NULL DEFAULT 0,
                    vat REAL NOT NULL DEFAULT 0,
                    total REAL NOT NULL DEFAULT 0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY(article_id) REFERENCES articles(id)
                        ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    method TEXT,
                    reference TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_invoices_customer
                    ON invoices(customer_id);
                CREATE INDEX IF NOT EXISTS idx_invoices_due_date
                    ON invoices(due_date);
                CREATE INDEX IF NOT EXISTS idx_payments_invoice
                    ON payments(invoice_id);

                CREATE TABLE IF NOT EXISTS company_settings (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    company_name TEXT NOT NULL DEFAULT 'JU-TAN Studio',
                    address TEXT,
                    postal_code TEXT,
                    city TEXT,
                    country TEXT NOT NULL DEFAULT 'Slovenija',
                    tax_number TEXT,
                    registration_number TEXT,
                    iban TEXT,
                    bank_name TEXT,
                    email TEXT,
                    phone TEXT,
                    website TEXT,
                    invoice_footer TEXT,
                    payment_terms_days INTEGER NOT NULL DEFAULT 15,
                    auto_backup INTEGER NOT NULL DEFAULT 1,
                    backup_retention_days INTEGER NOT NULL DEFAULT 30,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                INSERT OR IGNORE INTO company_settings(id, company_name)
                    VALUES(1, 'JU-TAN Studio');

                CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_code_unique
                    ON articles(code)
                    WHERE code IS NOT NULL AND code <> '';
                """
            )

        logger.info("SQLite baza inicializirana.")


db = Database()
