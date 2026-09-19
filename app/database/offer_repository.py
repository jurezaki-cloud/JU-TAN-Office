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
    ):
        from app.utils.vat import company_vat_liable, vat_liable_int

        self.ensure_schema()
        if vat_liable is None:
            vat_liable = company_vat_liable()
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO offers(

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
                vat_liable

            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (

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

        ))

        conn.commit()

        offer_id = cursor.lastrowid

        conn.close()

        return offer_id

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
    ):
        from app.utils.vat import vat_liable_int

        self.ensure_schema()
        if self.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)

        if vat_liable is None:
            vat_liable = self.get_vat_liable(offer_id)

        conn = db.connect()
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

        conn.commit()
        conn.close()

    def mark_converted(self, offer_id, invoice_id):
        """Record conversion linkage and set status to Sprejeta (immutable thereafter)."""
        self.ensure_schema()
        # Only the explicit column counts here: invoice notes already contain the
        # "[Iz ponudbe …]" marker at this point, which must not block linkage.
        if self.get_converted_invoice_id(offer_id, include_legacy=False):
            raise ValueError("Ponudba je že pretvorjena v račun.")

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE offers
            SET status=?, converted_invoice_id=?
            WHERE id=?
            """,
            ("Sprejeta", invoice_id, offer_id),
        )
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
    ):
        self.ensure_schema()
        if self.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)

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

        conn.commit()
        conn.close()

    def delete_items(self, offer_id):
        self.ensure_schema()
        if self.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM offer_items WHERE offer_id=?",
            (offer_id,),
        )

        conn.commit()
        conn.close()


offer_repository = OfferRepository()
