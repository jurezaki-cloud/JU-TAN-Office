from __future__ import annotations

from app.database.database import db

SUPPLIER_STATUSES = ("Active", "Inactive")


class SuppliersRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tax_number TEXT,
                contact TEXT,
                phone TEXT,
                email TEXT,
                status TEXT DEFAULT 'Active',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name)")
        conn.commit()
        conn.close()

    def get_all(self) -> list:
        self.ensure_schema()
        from app.modules.purchase.purchase_repository import purchase_repository
        purchase_repository.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                s.id,
                s.name,
                s.tax_number,
                s.contact,
                s.phone,
                s.email,
                s.status,
                IFNULL((
                    SELECT SUM(p.total)
                    FROM purchase_orders p
                    WHERE p.supplier_id = s.id
                      AND p.status NOT IN ('Draft', 'Cancelled')
                ), 0) AS turnover
            FROM suppliers s
            ORDER BY s.name COLLATE NOCASE
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_by_id(self, supplier_id: int):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, tax_number, contact, phone, email, status, notes
            FROM suppliers
            WHERE id=?
            """,
            (supplier_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row

    def search(self, text: str) -> list:
        self.ensure_schema()
        from app.modules.purchase.purchase_repository import purchase_repository
        purchase_repository.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        like = f"%{text}%"
        cursor.execute(
            """
            SELECT
                s.id,
                s.name,
                s.tax_number,
                s.contact,
                s.phone,
                s.email,
                s.status,
                IFNULL((
                    SELECT SUM(p.total)
                    FROM purchase_orders p
                    WHERE p.supplier_id = s.id
                      AND p.status NOT IN ('Draft', 'Cancelled')
                ), 0) AS turnover
            FROM suppliers s
            WHERE s.name LIKE ?
               OR IFNULL(s.tax_number, '') LIKE ?
               OR IFNULL(s.contact, '') LIKE ?
               OR IFNULL(s.email, '') LIKE ?
               OR IFNULL(s.phone, '') LIKE ?
            ORDER BY s.name COLLATE NOCASE
            """,
            (like, like, like, like, like),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add(
        self,
        name: str,
        tax_number: str,
        contact: str,
        phone: str,
        email: str,
        status: str,
        notes: str = "",
    ) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO suppliers(name, tax_number, contact, phone, email, status, notes)
            VALUES (?,?,?,?,?,?,?)
            """,
            (name, tax_number, contact, phone, email, status, notes),
        )
        conn.commit()
        supplier_id = cursor.lastrowid
        conn.close()
        return supplier_id

    def update(
        self,
        supplier_id: int,
        name: str,
        tax_number: str,
        contact: str,
        phone: str,
        email: str,
        status: str,
        notes: str = "",
    ) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE suppliers SET
                name=?, tax_number=?, contact=?, phone=?, email=?, status=?, notes=?
            WHERE id=?
            """,
            (name, tax_number, contact, phone, email, status, notes, supplier_id),
        )
        conn.commit()
        conn.close()

    def delete(self, supplier_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        conn.commit()
        conn.close()

    def count(self) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        value = int(cursor.fetchone()[0])
        conn.close()
        return value


suppliers_repository = SuppliersRepository()
