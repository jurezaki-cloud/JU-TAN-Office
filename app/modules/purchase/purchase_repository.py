from __future__ import annotations

from datetime import date

from app.database.database import db

PURCHASE_STATUSES = (
    "Draft",
    "Ordered",
    "Partially Received",
    "Received",
    "Cancelled",
)

OPEN_STATUSES = ("Draft", "Ordered", "Partially Received")
RECEIVABLE_STATUSES = ("Draft", "Ordered", "Partially Received")


class PurchaseRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        from app.modules.suppliers.suppliers_repository import suppliers_repository

        suppliers_repository.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL UNIQUE,
                supplier_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                delivery_date TEXT,
                status TEXT DEFAULT 'Draft',
                subtotal REAL DEFAULT 0,
                vat REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notes TEXT,
                last_received_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                article_id INTEGER,
                code TEXT,
                name TEXT,
                quantity REAL DEFAULT 1,
                qty_received REAL DEFAULT 0,
                price REAL DEFAULT 0,
                vat REAL DEFAULT 22,
                total REAL DEFAULT 0,
                FOREIGN KEY(purchase_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_items_po ON purchase_order_items(purchase_id)")
        conn.commit()
        conn.close()

    def get_all(self) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.id,
                p.number,
                s.name,
                p.issue_date,
                p.delivery_date,
                p.status,
                p.total,
                p.supplier_id,
                p.last_received_date
            FROM purchase_orders p
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            ORDER BY p.id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_by_id(self, purchase_id: int):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase_orders WHERE id=?", (purchase_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def search(self, text: str) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        like = f"%{text}%"
        cursor.execute(
            """
            SELECT
                p.id,
                p.number,
                s.name,
                p.issue_date,
                p.delivery_date,
                p.status,
                p.total,
                p.supplier_id,
                p.last_received_date
            FROM purchase_orders p
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.number LIKE ?
               OR IFNULL(s.name, '') LIKE ?
            ORDER BY p.id DESC
            """,
            (like, like),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_next_number(self) -> str:
        """Next PO number under a write lock (serialized peeks)."""
        self.ensure_schema()
        from app.database.database import db

        with db.transaction(immediate=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT number FROM purchase_orders
                WHERE number LIKE 'PO-%'
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row is None:
                return "PO-0001"
            try:
                number = int(str(row[0]).split("-")[-1]) + 1
            except (TypeError, ValueError):
                number = 1
            return f"PO-{number:04d}"

    def create(
        self,
        number: str,
        supplier_id: int,
        issue_date: str,
        delivery_date: str,
        status: str,
        subtotal: float,
        vat: float,
        total: float,
        notes: str,
    ) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO purchase_orders(
                number, supplier_id, issue_date, delivery_date, status,
                subtotal, vat, total, notes
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                number, supplier_id, issue_date, delivery_date, status,
                subtotal, vat, total, notes,
            ),
        )
        conn.commit()
        purchase_id = cursor.lastrowid
        conn.close()
        return purchase_id

    def update(
        self,
        purchase_id: int,
        supplier_id: int,
        issue_date: str,
        delivery_date: str,
        status: str,
        subtotal: float,
        vat: float,
        total: float,
        notes: str,
    ) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE purchase_orders SET
                supplier_id=?,
                issue_date=?,
                delivery_date=?,
                status=?,
                subtotal=?,
                vat=?,
                total=?,
                notes=?
            WHERE id=?
            """,
            (
                supplier_id, issue_date, delivery_date, status,
                subtotal, vat, total, notes, purchase_id,
            ),
        )
        conn.commit()
        conn.close()

    def delete(self, purchase_id: int) -> None:
        self.ensure_schema()
        self.delete_items(purchase_id)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM purchase_orders WHERE id=?", (purchase_id,))
        conn.commit()
        conn.close()

    def get_items(self, purchase_id: int) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, article_id, code, name, quantity, qty_received,
                price, vat, total
            FROM purchase_order_items
            WHERE purchase_id=?
            ORDER BY id
            """,
            (purchase_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_item(
        self,
        purchase_id: int,
        article_id,
        code: str,
        name: str,
        quantity: float,
        qty_received: float,
        price: float,
        vat: float,
        total: float,
    ) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO purchase_order_items(
                purchase_id, article_id, code, name, quantity, qty_received,
                price, vat, total
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                purchase_id, article_id, code, name, quantity, qty_received,
                price, vat, total,
            ),
        )
        conn.commit()
        conn.close()

    def delete_items(self, purchase_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM purchase_order_items WHERE purchase_id=?",
            (purchase_id,),
        )
        conn.commit()
        conn.close()

    def update_item_received(self, item_id: int, qty_received: float) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE purchase_order_items SET qty_received=? WHERE id=?",
            (qty_received, item_id),
        )
        conn.commit()
        conn.close()

    def set_status(
        self,
        purchase_id: int,
        status: str,
        last_received_date: str | None = None,
    ) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        if last_received_date is None:
            cursor.execute(
                "UPDATE purchase_orders SET status=? WHERE id=?",
                (status, purchase_id),
            )
        else:
            cursor.execute(
                """
                UPDATE purchase_orders
                SET status=?, last_received_date=?
                WHERE id=?
                """,
                (status, last_received_date, purchase_id),
            )
        conn.commit()
        conn.close()

    def kpis(self) -> dict:
        self.ensure_schema()
        from app.modules.suppliers.suppliers_repository import suppliers_repository

        today = date.today().isoformat()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM purchase_orders
            WHERE status IN ('Draft', 'Ordered', 'Partially Received')
            """
        )
        open_orders = int(cursor.fetchone()[0])
        cursor.execute(
            """
            SELECT COUNT(*) FROM purchase_orders
            WHERE last_received_date = ?
            """,
            (today,),
        )
        received_today = int(cursor.fetchone()[0])
        cursor.execute(
            """
            SELECT IFNULL(SUM(total), 0) FROM purchase_orders
            WHERE status != 'Cancelled'
            """
        )
        value = float(cursor.fetchone()[0] or 0)
        conn.close()
        return {
            "suppliers": suppliers_repository.count(),
            "open_orders": open_orders,
            "received_today": received_today,
            "value": value,
        }

    def analytics_snapshot(self) -> dict:
        """Podatki za Analytics (brez spremembe analytics modula)."""
        return self.kpis()


purchase_repository = PurchaseRepository()
