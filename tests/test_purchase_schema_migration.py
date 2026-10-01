import sqlite3

from app.database.database import db


def test_database_initialize_upgrades_purchase_discount(tmp_path):
    original_database = db.database
    db.dispose()
    db.database = tmp_path / "legacy.db"
    try:
        conn = sqlite3.connect(db.database)
        conn.execute(
            """CREATE TABLE purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                price REAL DEFAULT 0,
                vat REAL DEFAULT 22,
                total REAL DEFAULT 0
            )"""
        )
        conn.commit()
        conn.close()

        db.initialize()

        conn = sqlite3.connect(db.database)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(purchase_order_items)")}
        conn.close()
        assert "discount" in columns
    finally:
        db.dispose()
        db.database = original_database
