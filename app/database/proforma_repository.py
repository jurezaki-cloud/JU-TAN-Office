from __future__ import annotations

from datetime import date, timedelta

from app.database.database import db
from app.database.offer_repository import offer_repository


class ProformaRepository:
    def ensure_schema(self):
        conn = db.connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proformas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT NOT NULL UNIQUE,
                    offer_id INTEGER NOT NULL,
                    customer_id INTEGER,
                    issue_date TEXT NOT NULL,
                    due_date TEXT,
                    status TEXT NOT NULL DEFAULT 'Osnutek',
                    total REAL NOT NULL DEFAULT 0,
                    converted_invoice_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(proformas)").fetchall()}
            additions = {
                "subtotal": "REAL",
                "discount": "REAL",
                "vat": "REAL",
                "notes": "TEXT",
                "vat_liable": "INTEGER",
            }
            for name, sql_type in additions.items():
                if name not in columns:
                    conn.execute(f"ALTER TABLE proformas ADD COLUMN {name} {sql_type}")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proforma_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proforma_id INTEGER NOT NULL,
                    article_id INTEGER,
                    code TEXT,
                    name TEXT,
                    description TEXT,
                    quantity REAL,
                    unit TEXT,
                    price REAL,
                    discount REAL,
                    vat REAL,
                    total REAL,
                    FOREIGN KEY(proforma_id) REFERENCES proformas(id) ON DELETE CASCADE
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get_all(self):
        self.ensure_schema()
        conn = db.connect()
        try:
            return conn.execute("""
                SELECT p.id,p.number,c.company,p.issue_date,p.due_date,p.total,p.status,
                       p.offer_id,p.converted_invoice_id
                FROM proformas p LEFT JOIN customers c ON c.id=p.customer_id
                ORDER BY p.id DESC
            """).fetchall()
        finally:
            conn.close()

    def get_by_id(self, proforma_id):
        self.ensure_schema()
        conn = db.connect()
        try:
            return conn.execute("SELECT * FROM proformas WHERE id=?", (proforma_id,)).fetchone()
        finally:
            conn.close()

    def get_items(self, proforma_id):
        self.ensure_schema()
        conn = db.connect()
        try:
            return conn.execute("""
                SELECT id,article_id,code,name,description,quantity,unit,price,discount,vat,total
                FROM proforma_items WHERE proforma_id=? ORDER BY id
            """, (proforma_id,)).fetchall()
        finally:
            conn.close()

    def create_from_offer(self, offer_id):
        self.ensure_schema()
        offer = offer_repository.get_by_id(offer_id)
        if not offer:
            raise ValueError("Ponudba ne obstaja.")
        items = offer_repository.get_items(offer_id)
        if not items:
            raise ValueError("Ponudba nima postavk.")

        with db.transaction(immediate=True) as conn:
            existing = conn.execute("SELECT id FROM proformas WHERE offer_id=?", (offer_id,)).fetchone()
            if existing:
                return int(existing[0])
            next_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM proformas").fetchone()[0])
            number = f"PRED-{date.today().year}-{next_id:04d}"
            due = date.today() + timedelta(days=15)
            cur = conn.execute("""
                INSERT INTO proformas(
                    number,offer_id,customer_id,issue_date,due_date,status,total,
                    subtotal,discount,vat,notes,vat_liable
                ) VALUES(?,?,?,?,?,'Osnutek',?,?,?,?,?,?)
            """, (
                number, offer_id, offer[2], date.today().isoformat(), due.isoformat(),
                float(offer[9] or 0), float(offer[6] or 0), float(offer[7] or 0),
                float(offer[8] or 0), str(offer[10] or ""),
                1 if offer_repository.get_vat_liable(offer_id) else 0,
            ))
            proforma_id = int(cur.lastrowid)
            conn.executemany("""
                INSERT INTO proforma_items(
                    proforma_id,article_id,code,name,description,quantity,unit,price,discount,vat,total
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, [
                (proforma_id, row[1], row[2], row[3], row[4], row[5], row[6],
                 row[7], row[8], row[9], row[10])
                for row in items
            ])
            return proforma_id

    def mark_sent(self, proforma_id):
        self.ensure_schema()
        conn = db.connect()
        try:
            conn.execute("UPDATE proformas SET status='Poslan' WHERE id=? AND status='Osnutek'", (proforma_id,))
            conn.commit()
        finally:
            conn.close()

    def mark_converted(self, proforma_id, invoice_id):
        self.ensure_schema()
        conn = db.connect()
        try:
            conn.execute(
                "UPDATE proformas SET status='Pretvorjen', converted_invoice_id=? WHERE id=?",
                (invoice_id, proforma_id),
            )
            conn.commit()
        finally:
            conn.close()


proforma_repository = ProformaRepository()
