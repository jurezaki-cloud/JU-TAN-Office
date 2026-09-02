import sqlite3
from pathlib import Path

from app.core.constants import DATABASE_PATH
from app.core.logger import logger


class Database:

    def __init__(self):
        self.database = Path(DATABASE_PATH)

    def connect(self):
        conn = sqlite3.connect(self.database)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):

        conn = self.connect()
        cursor = conn.cursor()

        # =====================================================
        # CUSTOMERS
        # =====================================================

        cursor.execute("""
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
        )
        """)

        # =====================================================
        # ARTICLES
        # =====================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            code TEXT,
            name TEXT NOT NULL,
            description TEXT,

            unit TEXT,

            price REAL DEFAULT 0,

            vat REAL DEFAULT 22,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =====================================================
        # OFFERS
        # =====================================================

        cursor.execute("""
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
        )
        """)

        # =====================================================
        # OFFER ITEMS
        # =====================================================

        cursor.execute("""
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
        )
        """)

        conn.commit()
        conn.close()

        logger.info("SQLite baza inicializirana.")


db = Database()