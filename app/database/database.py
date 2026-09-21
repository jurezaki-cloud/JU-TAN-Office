import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.core.constants import DATABASE_PATH
from app.core.logger import logger


class _PooledConnection:
    """close() vrne povezavo v nabor (SQLite na nit)."""

    def __init__(self, raw: sqlite3.Connection) -> None:
        object.__setattr__(self, "_raw", raw)

    def close(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False

    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, "_raw"), name)


class Database:
    """SQLite povezava z WAL, PRAGMA uglašitvijo in naborom na nit."""

    def __init__(self) -> None:
        self.database = Path(DATABASE_PATH)
        self._local = threading.local()

    def connect(self):
        """Odpri ali ponovno uporabi povezavo niti."""
        raw = getattr(self._local, "conn", None)
        if raw is None:
            raw = sqlite3.connect(self.database, timeout=10)
            raw.execute("PRAGMA foreign_keys = ON")
            raw.execute("PRAGMA journal_mode = WAL")
            raw.execute("PRAGMA busy_timeout = 5000")
            raw.execute("PRAGMA synchronous = NORMAL")
            raw.execute("PRAGMA temp_store = MEMORY")
            raw.execute("PRAGMA cache_size = -8000")
            raw.execute("PRAGMA mmap_size = 268435456")
            self._local.conn = raw
        return _PooledConnection(raw)

    def dispose(self) -> None:
        raw = getattr(self._local, "conn", None)
        if raw is not None:
            try:
                raw.close()
            except sqlite3.Error:
                pass
            self._local.conn = None

    @contextmanager
    def transaction(self, *, immediate: bool = False):
        """Own commit/rollback for a unit of work.

        Leaf repository methods must accept an optional ``conn`` and must not
        call ``commit()`` / ``rollback()`` when joined to this outer transaction.
        ``immediate=True`` uses BEGIN IMMEDIATE so writers serialize before the
        first SELECT (required for atomic document-number allocation).
        """
        conn = self.connect()
        raw = object.__getattribute__(conn, "_raw")
        previous_isolation = raw.isolation_level
        try:
            raw.isolation_level = None
            raw.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield conn
            raw.commit()
        except Exception:
            try:
                raw.rollback()
            except sqlite3.Error:
                pass
            raise
        finally:
            raw.isolation_level = previous_isolation
            conn.close()

    def initialize(self):

        conn = self.connect()
        cursor = conn.cursor()

        # =====================================================
        # COMPANY
        # =====================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company (

            id INTEGER PRIMARY KEY CHECK(id = 1),

            name TEXT,
            legal_name TEXT,

            address TEXT,
            postal_code TEXT,
            city TEXT,
            country TEXT,

            tax_number TEXT,
            registration_number TEXT,

            iban TEXT,
            bank TEXT,

            email TEXT,
            website TEXT,
            phone TEXT,
            mobile TEXT,

            logo TEXT,

            invoice_prefix TEXT DEFAULT 'RAC',
            offer_prefix TEXT DEFAULT 'PON',

            invoice_counter INTEGER DEFAULT 1,
            offer_counter INTEGER DEFAULT 1,

            default_vat REAL DEFAULT 22,

            notes TEXT,

            vat_liable INTEGER DEFAULT 1,

            signature_path TEXT,
            stamp_path TEXT,
            doc_primary_color TEXT DEFAULT '#0F172A',
            doc_accent_color TEXT DEFAULT '#059669',
            doc_table_header_color TEXT DEFAULT '#F1F5F9',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        INSERT OR IGNORE INTO company(id)
        VALUES (1)
        """)

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

            converted_invoice_id INTEGER,

            vat_liable INTEGER DEFAULT 1,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(customer_id)
                REFERENCES customers(id)
                ON DELETE RESTRICT
        )
        """)

        # =====================================================
        # OFFER ITEMS
        # =====================================================
                # =====================================================
        # INVOICES
        # =====================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            invoice_number TEXT NOT NULL UNIQUE,

            customer_id INTEGER NOT NULL,

            issue_date TEXT NOT NULL,

            due_date TEXT,

            status TEXT DEFAULT 'Osnutek',

            subtotal REAL DEFAULT 0,

            discount REAL DEFAULT 0,

            vat REAL DEFAULT 0,

            total REAL DEFAULT 0,

            notes TEXT,

            vat_liable INTEGER DEFAULT 1,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(customer_id)
                REFERENCES customers(id)
                ON DELETE RESTRICT
        )
        """)

        # =====================================================
        # INVOICE ITEMS
        # =====================================================

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            invoice_id INTEGER NOT NULL,

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

            FOREIGN KEY(invoice_id)
                REFERENCES invoices(id)
                ON DELETE CASCADE,

            FOREIGN KEY(article_id)
                REFERENCES articles(id)
                ON DELETE SET NULL
        )
        """)
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

        # Compatibility migration: Phase-8/main used invoices.number while the
        # full Office repositories use invoices.invoice_number. Preserve existing
        # business data and add/backfill the canonical column before indexes or UI
        # queries run. This is intentionally idempotent.
        invoice_cols = {
            row[1] for row in cursor.execute("PRAGMA table_info(invoices)").fetchall()
        }
        if "invoice_number" not in invoice_cols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_number TEXT")
            if "number" in invoice_cols:
                cursor.execute(
                    "UPDATE invoices SET invoice_number=number "
                    "WHERE invoice_number IS NULL OR invoice_number=''"
                )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_invoices_invoice_number_unique "
            "ON invoices(invoice_number) WHERE invoice_number IS NOT NULL AND invoice_number <> ''"
        )

        payment_cols = {
            row[1] for row in cursor.execute("PRAGMA table_info(payments)").fetchall()
        }
        if payment_cols and "paid_date" not in payment_cols:
            cursor.execute("ALTER TABLE payments ADD COLUMN paid_date TEXT")
            if "payment_date" in payment_cols:
                cursor.execute(
                    "UPDATE payments SET paid_date=payment_date "
                    "WHERE paid_date IS NULL OR paid_date=''"
                )

        for sql in (
            "CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company)",
            "CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_contact ON customers(contact)",
            "CREATE INDEX IF NOT EXISTS idx_articles_name ON articles(name)",
            "CREATE INDEX IF NOT EXISTS idx_articles_code ON articles(code)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON invoices(issue_date)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)",
            "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id)",
            "CREATE INDEX IF NOT EXISTS idx_offers_customer ON offers(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_offers_number ON offers(number)",
            "CREATE INDEX IF NOT EXISTS idx_offers_issue_date ON offers(issue_date)",
            "CREATE INDEX IF NOT EXISTS idx_offer_items_offer ON offer_items(offer_id)",
        ):
            cursor.execute(sql)
        for extra in (
            "CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind)",
            "CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)",
        ):
            try:
                cursor.execute(extra)
            except sqlite3.OperationalError:
                pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                username TEXT,
                action TEXT NOT NULL,
                detail TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                paid_date TEXT NOT NULL,
                amount REAL NOT NULL,
                method TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id)"
        )

        try:
            from app.core.search_engine import ensure_search_schema
            ensure_search_schema(conn)
        except Exception:
            logger.debug("FTS5 ni na voljo.", exc_info=True)

        conn.commit()
        conn.close()

        try:
            from app.database.company_repository import company_repository
            company_repository.ensure_schema()
        except Exception:
            logger.debug("Company schema upgrade skipped.", exc_info=True)

        try:
            from app.database.offer_repository import offer_repository
            offer_repository.ensure_schema()
        except Exception:
            logger.debug("Offer schema upgrade skipped.", exc_info=True)

        try:
            from app.database.invoice_repository import invoice_repository
            invoice_repository.ensure_schema()
        except Exception:
            logger.debug("Invoice schema upgrade skipped.", exc_info=True)

        try:
            from app.database.order_repository import order_repository
            order_repository.ensure_schema()
        except Exception:
            logger.debug("Order schema upgrade skipped.", exc_info=True)

        try:
            from app.database.user_repository import user_repository
            user_repository.ensure_schema()
        except Exception:
            logger.debug("Users schema upgrade skipped.", exc_info=True)

        logger.info("SQLite baza inicializirana.")


db = Database()