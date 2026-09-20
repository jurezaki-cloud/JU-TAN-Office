import sqlite3
from contextlib import contextmanager

from license_server.config import DATABASE_PATH


class LicenseDatabase:
    def __init__(self, path=DATABASE_PATH):
        self.path = path

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def transaction(self, immediate=False):
        connection = self.connect()
        try:
            if immediate:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS licenses (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    key_hint TEXT NOT NULL,
                    plan TEXT NOT NULL,
                    max_devices INTEGER NOT NULL CHECK(max_devices > 0),
                    status TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                );
                CREATE TABLE IF NOT EXISTS activations (
                    id TEXT PRIMARY KEY,
                    license_id TEXT NOT NULL,
                    installation_id TEXT NOT NULL,
                    platform TEXT,
                    app_version TEXT,
                    status TEXT NOT NULL,
                    activated_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    deactivated_at TEXT,
                    UNIQUE(license_id, installation_id),
                    FOREIGN KEY(license_id) REFERENCES licenses(id)
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    entity_id TEXT,
                    detail TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_activations_license
                    ON activations(license_id, status);
                CREATE INDEX IF NOT EXISTS idx_activations_last_seen
                    ON activations(last_seen_at);
                """
            )
