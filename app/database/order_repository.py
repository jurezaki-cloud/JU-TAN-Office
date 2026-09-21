from app.database.database import db


class OrderRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                delivery_date TEXT,
                status TEXT DEFAULT 'Osnutek',
                subtotal REAL DEFAULT 0,
                discount REAL DEFAULT 0,
                vat REAL DEFAULT 0,
                total REAL DEFAULT 0,
                notes TEXT,
                vat_liable INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
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
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE SET NULL
            )
        """)
        cols = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(orders)").fetchall()
        }
        if cols and "vat_liable" not in cols:
            cursor.execute(
                "ALTER TABLE orders ADD COLUMN vat_liable INTEGER DEFAULT 1"
            )
            cursor.execute(
                "UPDATE orders SET vat_liable=1 WHERE vat_liable IS NULL"
            )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")
        conn.commit()
        conn.close()

    def get_vat_liable(self, order_id) -> bool:
        from app.utils.vat import parse_vat_liable

        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT vat_liable FROM orders WHERE id=?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return True
        return parse_vat_liable(row[0])

    def get_all(self):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                o.id,
                o.number,
                c.company,
                o.issue_date,
                o.delivery_date,
                o.status,
                o.total
            FROM orders o
            LEFT JOIN customers c ON c.id = o.customer_id
            ORDER BY o.id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_by_id(self, order_id):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def search(self, text):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        like = f"%{text}%"
        cursor.execute("""
            SELECT
                o.id,
                o.number,
                c.company,
                o.issue_date,
                o.delivery_date,
                o.status,
                o.total
            FROM orders o
            LEFT JOIN customers c ON c.id = o.customer_id
            WHERE o.number LIKE ?
               OR IFNULL(c.company, '') LIKE ?
            ORDER BY o.id DESC
        """, (like, like))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _next_number_on_conn(self, conn) -> str:
        """Compute next order number under an open write lock."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT number FROM orders
            WHERE number LIKE 'NAR%'
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row is None:
            return "NAR-0001"
        try:
            number = int(str(row[0]).split("-")[-1]) + 1
        except (TypeError, ValueError):
            number = 1
        return f"NAR-{number:04d}"

    def get_next_number(self):
        """Peek next order number for UI preview; does not consume it."""
        self.ensure_schema()
        with db.transaction(immediate=True) as conn:
            return self._next_number_on_conn(conn)

    @staticmethod
    def _validate_create(customer_id, items) -> None:
        if not customer_id:
            raise ValueError("Stranka je obvezna.")
        if not items:
            raise ValueError("Dokument mora vsebovati vsaj eno postavko.")
        for item in items:
            if not str(item.get("name") or "").strip():
                raise ValueError("Postavka mora imeti naziv.")
            if float(item.get("quantity") or 0) <= 0:
                raise ValueError("Količina postavke mora biti večja od 0.")

    def _insert_on_conn(
        self,
        conn,
        number,
        customer_id,
        issue_date,
        delivery_date,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        vat_liable,
    ) -> tuple[int, str]:
        from app.utils.vat import vat_liable_int

        if not number:
            number = self._next_number_on_conn(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders(
                number, customer_id, issue_date, delivery_date, status,
                subtotal, discount, vat, total, notes, vat_liable
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                number, customer_id, issue_date, delivery_date, status,
                subtotal, discount, vat, total, notes, vat_liable_int(vat_liable),
            ),
        )
        return cursor.lastrowid, number

    def create(
        self,
        number,
        customer_id,
        issue_date,
        delivery_date,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        vat_liable=None,
        conn=None,
    ):
        from app.utils.vat import company_vat_liable

        self.ensure_schema()
        if vat_liable is None:
            vat_liable = company_vat_liable()

        def _run(txn):
            order_id, _ = self._insert_on_conn(
                txn,
                number,
                customer_id,
                issue_date,
                delivery_date,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable,
            )
            return order_id

        if conn is not None:
            return _run(conn)
        with db.transaction(immediate=True) as txn:
            return _run(txn)

    def create_with_items(
        self,
        number,
        customer_id,
        issue_date,
        delivery_date,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        items,
        vat_liable=None,
    ) -> tuple[int, str]:
        """Allocate number + insert order header and items in one transaction."""
        from app.utils.vat import company_vat_liable

        self.ensure_schema()
        self._validate_create(customer_id, items)
        if vat_liable is None:
            vat_liable = company_vat_liable()

        with db.transaction(immediate=True) as conn:
            order_id, number = self._insert_on_conn(
                conn,
                number,
                customer_id,
                issue_date,
                delivery_date,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable,
            )
            for item in items:
                self.add_item(
                    order_id=order_id,
                    article_id=item.get("article_id"),
                    code=item.get("code") or "",
                    name=item.get("name") or "",
                    description=item.get("description") or "",
                    quantity=item.get("quantity"),
                    unit=item.get("unit") or "",
                    price=item.get("price"),
                    discount=item.get("discount") or 0,
                    vat=item.get("vat") or 0,
                    total=item.get("total"),
                    conn=conn,
                )
            counted = conn.execute(
                "SELECT COUNT(*) FROM order_items WHERE order_id=?",
                (order_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke naročila niso bile shranjene.")
            return order_id, number

    def update(
        self,
        order_id,
        customer_id,
        issue_date,
        delivery_date,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        vat_liable=None,
        conn=None,
    ):
        from app.utils.vat import vat_liable_int

        owns = conn is None
        if owns:
            self.ensure_schema()
            if vat_liable is None:
                vat_liable = self.get_vat_liable(order_id)
            conn = self._connect()
        elif vat_liable is None:
            raise ValueError("vat_liable je obvezen znotraj zunanje transakcije.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders SET
                customer_id=?,
                issue_date=?,
                delivery_date=?,
                status=?,
                subtotal=?,
                discount=?,
                vat=?,
                total=?,
                notes=?,
                vat_liable=?
            WHERE id=?
        """, (
            customer_id, issue_date, delivery_date, status,
            subtotal, discount, vat, total, notes, vat_liable_int(vat_liable), order_id,
        ))
        if owns:
            conn.commit()
            conn.close()

    def update_with_items(
        self,
        order_id,
        customer_id,
        issue_date,
        delivery_date,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        items,
        vat_liable=None,
    ) -> None:
        """Update header + replace items in one transaction (GOLD-3B)."""
        self.ensure_schema()
        self._validate_create(customer_id, items)
        if vat_liable is None:
            vat_liable = self.get_vat_liable(order_id)

        with db.transaction(immediate=True) as conn:
            self.update(
                order_id,
                customer_id,
                issue_date,
                delivery_date,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable=vat_liable,
                conn=conn,
            )
            self.delete_items(order_id, conn=conn)
            for item in items:
                self.add_item(
                    order_id=order_id,
                    article_id=item.get("article_id"),
                    code=item.get("code") or "",
                    name=item.get("name") or "",
                    description=item.get("description") or "",
                    quantity=item.get("quantity"),
                    unit=item.get("unit") or "",
                    price=item.get("price"),
                    discount=item.get("discount") or 0,
                    vat=item.get("vat") or 0,
                    total=item.get("total"),
                    conn=conn,
                )
            counted = conn.execute(
                "SELECT COUNT(*) FROM order_items WHERE order_id=?",
                (order_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke naročila niso bile shranjene.")

    def delete(self, order_id):
        self.ensure_schema()
        self.delete_items(order_id)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()
        conn.close()

    def get_items(self, order_id):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id, article_id, code, name, description,
                quantity, unit, price, discount, vat, total
            FROM order_items
            WHERE order_id=?
            ORDER BY id
        """, (order_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_item(
        self,
        order_id,
        article_id,
        code,
        name,
        description,
        quantity,
        unit,
        price,
        discount,
        vat,
        total,
        conn=None,
    ):
        owns = conn is None
        if owns:
            self.ensure_schema()
            conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO order_items(
                order_id, article_id, code, name, description,
                quantity, unit, price, discount, vat, total
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            order_id, article_id, code, name, description,
            quantity, unit, price, discount, vat, total,
        ))
        if owns:
            conn.commit()
            conn.close()

    def delete_items(self, order_id, conn=None):
        owns = conn is None
        if owns:
            self.ensure_schema()
            conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
        if owns:
            conn.commit()
            conn.close()


order_repository = OrderRepository()
