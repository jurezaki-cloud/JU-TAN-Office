from __future__ import annotations

from app.database.database import db


class TravelOrderRepository:
    def ensure_schema(self) -> None:
        conn = db.connect()
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS travel_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL UNIQUE,
            employee TEXT NOT NULL,
            purpose TEXT,
            route TEXT NOT NULL,
            vehicle TEXT,
            registration TEXT,
            departure_at TEXT,
            return_at TEXT,
            start_km REAL DEFAULT 0,
            end_km REAL DEFAULT 0,
            distance_km REAL DEFAULT 0,
            mileage_rate REAL DEFAULT 0,
            mileage_amount REAL DEFAULT 0,
            per_diem_amount REAL DEFAULT 0,
            parking REAL DEFAULT 0,
            tolls REAL DEFAULT 0,
            fuel REAL DEFAULT 0,
            other_costs REAL DEFAULT 0,
            advance REAL DEFAULT 0,
            total REAL DEFAULT 0,
            settlement REAL DEFAULT 0,
            status TEXT DEFAULT 'Osnutek',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_travel_orders_number ON travel_orders(number);
        CREATE INDEX IF NOT EXISTS idx_travel_orders_employee ON travel_orders(employee);
        CREATE INDEX IF NOT EXISTS idx_travel_orders_departure ON travel_orders(departure_at);
        """)
        conn.commit(); conn.close()

    def get_all(self):
        self.ensure_schema()
        conn=db.connect()
        rows=conn.execute("""SELECT id, number, employee, route, departure_at, return_at,
            distance_km, total, status FROM travel_orders ORDER BY id DESC""").fetchall()
        conn.close()
        return rows

    def get_by_id(self, order_id):
        self.ensure_schema(); conn=db.connect()
        row=conn.execute("SELECT * FROM travel_orders WHERE id=?", (order_id,)).fetchone()
        conn.close(); return row

    def _next_number_on_conn(self, conn) -> str:
        row = conn.execute(
            "SELECT COALESCE(MAX(id),0)+1 FROM travel_orders"
        ).fetchone()
        return f"PN-{int(row[0]):05d}"

    def next_number(self) -> str:
        """Peek next travel-order number for UI preview; does not reserve."""
        self.ensure_schema()
        with db.transaction(immediate=True) as conn:
            return self._next_number_on_conn(conn)

    def save(self, data: dict, order_id=None) -> int:
        self.ensure_schema()
        fields = (
            "number", "employee", "purpose", "route", "vehicle", "registration",
            "departure_at", "return_at", "start_km", "end_km", "distance_km",
            "mileage_rate", "mileage_amount", "per_diem_amount", "parking", "tolls",
            "fuel", "other_costs", "advance", "total", "settlement", "status", "notes",
        )
        employee = str(data.get("employee") or "").strip()
        route = str(data.get("route") or "").strip()
        if not employee or not route:
            raise ValueError("Zaposleni in relacija sta obvezna.")

        with db.transaction(immediate=True) as conn:
            if order_id is None:
                payload = dict(data)
                payload["employee"] = employee
                payload["route"] = route
                if not payload.get("number"):
                    payload["number"] = self._next_number_on_conn(conn)
                values = [payload.get(k) for k in fields]
                marks = ",".join("?" for _ in fields)
                cur = conn.execute(
                    f"INSERT INTO travel_orders ({','.join(fields)}) VALUES ({marks})",
                    values,
                )
                order_id = cur.lastrowid
                # Travel orders have no line-items table; validate header persisted.
                saved = conn.execute(
                    "SELECT employee, route FROM travel_orders WHERE id=?",
                    (order_id,),
                ).fetchone()
                if saved is None or not saved[0] or not saved[1]:
                    raise RuntimeError("Potni nalog ni bil shranjen.")
            else:
                values = [data.get(k) for k in fields]
                current = conn.execute(
                    "SELECT status FROM travel_orders WHERE id=?",
                    (order_id,),
                ).fetchone()
                if current is None:
                    raise ValueError("Potni nalog ne obstaja.")
                if (current[0] or "") in ("Zaključen", "Storniran"):
                    raise ValueError(
                        "Zaključenega ali storniranega potnega naloga ni mogoče spreminjati."
                    )
                assigns = ",".join(f"{k}=?" for k in fields)
                conn.execute(
                    f"UPDATE travel_orders SET {assigns} WHERE id=?",
                    values + [order_id],
                )
        return int(order_id)

    def cancel(self, order_id) -> None:
        self.ensure_schema(); conn=db.connect()
        conn.execute("UPDATE travel_orders SET status='Storniran' WHERE id=?", (order_id,))
        conn.commit(); conn.close()


travel_order_repository = TravelOrderRepository()
