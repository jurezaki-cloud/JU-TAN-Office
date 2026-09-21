from app.database.database import db


CONVERTED_OFFER_MESSAGE = (
    "Ponudba je že pretvorjena v račun in je ni mogoče spreminjati."
)


class OfferRepository:

    # ==========================
    # PONUDBE
    # ==========================

    def ensure_schema(self):
        """Ensure offers.converted_invoice_id and vat_liable exist (new and existing DBs)."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='offers'"
        )
        if cursor.fetchone():
            cols = {
                row[1]
                for row in cursor.execute("PRAGMA table_info(offers)").fetchall()
            }
            if "converted_invoice_id" not in cols:
                cursor.execute(
                    "ALTER TABLE offers ADD COLUMN converted_invoice_id INTEGER"
                )
            if "vat_liable" not in cols:
                cursor.execute(
                    "ALTER TABLE offers ADD COLUMN vat_liable INTEGER DEFAULT 1"
                )
                cursor.execute(
                    "UPDATE offers SET vat_liable=1 WHERE vat_liable IS NULL"
                )
        conn.commit()
        conn.close()

    def get_vat_liable(self, offer_id) -> bool:
        from app.utils.vat import parse_vat_liable

        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT vat_liable FROM offers WHERE id=?", (offer_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return True
        return parse_vat_liable(row[0])

    def get_all(self):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.number,
                c.company,
                o.issue_date,
                o.valid_until,
                o.status,
                o.total
            FROM offers o
            LEFT JOIN customers c
                ON c.id = o.customer_id
            ORDER BY o.id DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    def get_by_id(self, offer_id):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM offers
            WHERE id=?
        """, (offer_id,))

        row = cursor.fetchone()

        conn.close()

        return row

    def get_converted_invoice_id(self, offer_id, *, include_legacy: bool = True):
        """Return linked invoice id if this offer was converted, else None."""
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT converted_invoice_id, number FROM offers WHERE id=?",
            (offer_id,),
        )
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return None
        if row[0]:
            conn.close()
            return int(row[0])

        if not include_legacy:
            conn.close()
            return None

        # Legacy fallback: invoices created before converted_invoice_id existed.
        number = row[1] or ""
        if not number:
            conn.close()
            return None
        marker = f"[Iz ponudbe {number}]"
        cursor.execute(
            "SELECT id FROM invoices WHERE IFNULL(notes, '') LIKE ? ORDER BY id LIMIT 1",
            (f"%{marker}%",),
        )
        legacy = cursor.fetchone()
        conn.close()
        return int(legacy[0]) if legacy else None

    def is_converted(self, offer_id) -> bool:
        return self.get_converted_invoice_id(offer_id) is not None

    def _next_number_on_conn(self, conn) -> str:
        """Compute next offer number under an open write lock (does not reserve alone)."""
        from datetime import datetime

        year = datetime.now().year
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT number
            FROM offers
            WHERE number LIKE ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (f"P-{year}-%",),
        )
        row = cursor.fetchone()
        if row is None:
            return f"P-{year}-000001"
        last = row[0]
        try:
            number = int(str(last).split("-")[-1]) + 1
        except Exception:
            number = 1
        return f"P-{year}-{number:06d}"

    def get_next_number(self) -> str:
        """Peek next offer number for UI preview; does not consume it."""
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
        valid_until,
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
            INSERT INTO offers(
                number, customer_id, issue_date, valid_until, status,
                subtotal, discount, vat, total, notes, vat_liable
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                number,
                customer_id,
                issue_date,
                valid_until,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable_int(vat_liable),
            ),
        )
        return cursor.lastrowid, number

    def create(
        self,
        number,
        customer_id,
        issue_date,
        valid_until,
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
            offer_id, _ = self._insert_on_conn(
                txn,
                number,
                customer_id,
                issue_date,
                valid_until,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable,
            )
            return offer_id

        if conn is not None:
            return _run(conn)
        with db.transaction(immediate=True) as txn:
            return _run(txn)

    def create_with_items(
        self,
        number,
        customer_id,
        issue_date,
        valid_until,
        status,
        subtotal,
        discount,
        vat,
        total,
        notes,
        items,
        vat_liable=None,
    ) -> tuple[int, str]:
        """Allocate number + insert offer header and items in one transaction."""
        from app.utils.vat import company_vat_liable

        self.ensure_schema()
        self._validate_create(customer_id, items)
        if vat_liable is None:
            vat_liable = company_vat_liable()

        with db.transaction(immediate=True) as conn:
            offer_id, number = self._insert_on_conn(
                conn,
                number,
                customer_id,
                issue_date,
                valid_until,
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
                    offer_id=offer_id,
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
                "SELECT COUNT(*) FROM offer_items WHERE offer_id=?",
                (offer_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke ponudbe niso bile shranjene.")
            return offer_id, number

    def update(
        self,
        offer_id,
        customer_id,
        issue_date,
        valid_until,
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
            if self.is_converted(offer_id):
                raise ValueError(CONVERTED_OFFER_MESSAGE)
            if vat_liable is None:
                vat_liable = self.get_vat_liable(offer_id)
            conn = db.connect()
        elif vat_liable is None:
            raise ValueError("vat_liable je obvezen znotraj zunanje transakcije.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE offers
            SET

                customer_id=?,
                issue_date=?,
                valid_until=?,
                status=?,

                subtotal=?,
                discount=?,
                vat=?,
                total=?,

                notes=?,
                vat_liable=?

            WHERE id=?

        """, (

            customer_id,
            issue_date,
            valid_until,
            status,

            subtotal,
            discount,
            vat,
            total,

            notes,
            vat_liable_int(vat_liable),

            offer_id,

        ))

        if owns:
            conn.commit()
            conn.close()

    def update_with_items(
        self,
        offer_id,
        customer_id,
        issue_date,
        valid_until,
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
        if self.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)
        self._validate_create(customer_id, items)
        if vat_liable is None:
            vat_liable = self.get_vat_liable(offer_id)

        with db.transaction(immediate=True) as conn:
            self.update(
                offer_id,
                customer_id,
                issue_date,
                valid_until,
                status,
                subtotal,
                discount,
                vat,
                total,
                notes,
                vat_liable=vat_liable,
                conn=conn,
            )
            self.delete_items(offer_id, conn=conn)
            for item in items:
                self.add_item(
                    offer_id=offer_id,
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
                "SELECT COUNT(*) FROM offer_items WHERE offer_id=?",
                (offer_id,),
            ).fetchone()[0]
            if int(counted) != len(items):
                raise RuntimeError("Postavke ponudbe niso bile shranjene.")

    def mark_converted(self, offer_id, invoice_id, conn=None):
        """Record conversion linkage and set status to Sprejeta (immutable thereafter)."""
        # Only the explicit column counts here: invoice notes already contain the
        # "[Iz ponudbe …]" marker at this point, which must not block linkage.
        owns = conn is None
        if owns:
            self.ensure_schema()
            if self.get_converted_invoice_id(offer_id, include_legacy=False):
                raise ValueError("Ponudba je že pretvorjena v račun.")
            conn = db.connect()
        cursor = conn.cursor()
        if not owns:
            row = cursor.execute(
                "SELECT converted_invoice_id FROM offers WHERE id=?",
                (offer_id,),
            ).fetchone()
            if row and row[0] is not None:
                raise ValueError("Ponudba je že pretvorjena v račun.")
        cursor.execute(
            """
            UPDATE offers
            SET status=?, converted_invoice_id=?
            WHERE id=?
            """,
            ("Sprejeta", invoice_id, offer_id),
        )
        if owns:
            conn.commit()
            conn.close()

    def delete(self, offer_id):
        self.ensure_schema()
        if self.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM offers WHERE id=?",
            (offer_id,),
        )

        conn.commit()
        conn.close()

    # ==========================
    # POSTAVKE PONUDBE
    # ==========================

    def get_items(self, offer_id):
        self.ensure_schema()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                article_id,
                code,
                name,
                description,
                quantity,
                unit,
                price,
                discount,
                vat,
                total
            FROM offer_items
            WHERE offer_id=?
            ORDER BY id
        """, (offer_id,))

        rows = cursor.fetchall()

        conn.close()

        return rows

    def add_item(
        self,
        offer_id,
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
        if conn is None:
            self.ensure_schema()
            if self.is_converted(offer_id):
                raise ValueError(CONVERTED_OFFER_MESSAGE)

        owns = conn is None
        if owns:
            conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO offer_items(

                offer_id,
                article_id,
                code,
                name,
                description,
                quantity,
                unit,
                price,
                discount,
                vat,
                total

            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)

        """, (

            offer_id,
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

        ))

        if owns:
            conn.commit()
            conn.close()

    def delete_items(self, offer_id, conn=None):
        owns = conn is None
        if owns:
            self.ensure_schema()
            if self.is_converted(offer_id):
                raise ValueError(CONVERTED_OFFER_MESSAGE)
            conn = db.connect()

        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM offer_items WHERE offer_id=?",
            (offer_id,),
        )
        if owns:
            conn.commit()
            conn.close()


offer_repository = OfferRepository()
