from __future__ import annotations

from datetime import datetime

from app.database.database import db

STAGES = (
    "Lead",
    "Qualified",
    "Proposal",
    "Negotiation",
    "Won",
    "Lost",
)
ACTIVITY_TYPES = (
    "Call",
    "Email",
    "Meeting",
    "Task",
    "Visit",
    "Note",
    "Reminder",
)
PRIORITIES = ("Low", "Normal", "High", "Urgent")
DEAL_STATUSES = ("Active", "Won", "Lost")


class CrmRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                company TEXT,
                contact TEXT,
                email TEXT,
                phone TEXT,
                vat TEXT,
                salesperson TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_pipeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                contact_id INTEGER,
                title TEXT NOT NULL,
                company TEXT,
                stage TEXT DEFAULT 'Lead',
                salesperson TEXT,
                priority TEXT DEFAULT 'Normal',
                value REAL DEFAULT 0,
                status TEXT DEFAULT 'Active',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                contact_id INTEGER,
                pipeline_id INTEGER,
                type TEXT NOT NULL,
                title TEXT,
                due_date TEXT,
                salesperson TEXT,
                priority TEXT DEFAULT 'Normal',
                is_done INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crm_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                pipeline_id INTEGER,
                body TEXT NOT NULL,
                owner TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_pipeline_stage ON crm_pipeline(stage)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_crm_activities_deal ON crm_activities(pipeline_id)")
        conn.commit()
        conn.close()

    def add_contact(self, **fields) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO crm_contacts(
                customer_id, company, contact, email, phone, vat, salesperson, created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                fields.get("customer_id"),
                fields.get("company") or "",
                fields.get("contact") or "",
                fields.get("email") or "",
                fields.get("phone") or "",
                fields.get("vat") or "",
                fields.get("salesperson") or "",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        contact_id = cursor.lastrowid
        conn.close()
        return contact_id

    def contacts(self) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_contacts ORDER BY company COLLATE NOCASE")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_deal(self, **fields) -> int:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        stage = fields.get("stage") or "Lead"
        status = _status_for(stage)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO crm_pipeline(
                customer_id, contact_id, title, company, stage, salesperson,
                priority, value, status, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                fields.get("customer_id"),
                fields.get("contact_id"),
                fields.get("title") or "Lead",
                fields.get("company") or "",
                stage,
                fields.get("salesperson") or "",
                fields.get("priority") or "Normal",
                float(fields.get("value") or 0),
                status,
                now,
                now,
            ),
        )
        conn.commit()
        deal_id = cursor.lastrowid
        conn.close()
        return deal_id

    def deals(self) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_pipeline ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_deal(self, deal_id: int):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crm_pipeline WHERE id=?", (deal_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def set_stage(self, deal_id: int, stage: str) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE crm_pipeline
            SET stage=?, status=?, updated_at=?
            WHERE id=?
            """,
            (stage, _status_for(stage), datetime.now().isoformat(timespec="seconds"), deal_id),
        )
        conn.commit()
        conn.close()

    def add_activity(self, **fields) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO crm_activities(
                customer_id, contact_id, pipeline_id, type, title, due_date,
                salesperson, priority, is_done, notes, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                fields.get("customer_id"),
                fields.get("contact_id"),
                fields.get("pipeline_id"),
                fields.get("type") or "Note",
                fields.get("title") or "",
                fields.get("due_date") or "",
                fields.get("salesperson") or "",
                fields.get("priority") or "Normal",
                1 if fields.get("is_done") else 0,
                fields.get("notes") or "",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        activity_id = cursor.lastrowid
        conn.close()
        return activity_id

    def activities(self, customer_id: int | None = None) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        if customer_id is None:
            cursor.execute("SELECT * FROM crm_activities ORDER BY id DESC")
        else:
            cursor.execute(
                "SELECT * FROM crm_activities WHERE customer_id=? ORDER BY id DESC",
                (customer_id,),
            )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_note(self, customer_id, pipeline_id, body: str, owner: str) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO crm_notes(customer_id, pipeline_id, body, owner, created_at)
            VALUES (?,?,?,?,?)
            """,
            (
                customer_id,
                pipeline_id,
                body,
                owner,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()
        return note_id

    def notes(self, customer_id: int | None = None) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        if customer_id is None:
            cursor.execute("SELECT * FROM crm_notes ORDER BY id DESC")
        else:
            cursor.execute(
                "SELECT * FROM crm_notes WHERE customer_id=? ORDER BY id DESC",
                (customer_id,),
            )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def salespeople(self) -> list[str]:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT salesperson FROM crm_pipeline WHERE IFNULL(salesperson,'') != ''
            UNION
            SELECT salesperson FROM crm_activities WHERE IFNULL(salesperson,'') != ''
            UNION
            SELECT salesperson FROM crm_contacts WHERE IFNULL(salesperson,'') != ''
            ORDER BY 1 COLLATE NOCASE
            """
        )
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rows

    def delete_deal(self, deal_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crm_pipeline WHERE id=?", (deal_id,))
        conn.commit()
        conn.close()


def _status_for(stage: str) -> str:
    if stage == "Won":
        return "Won"
    if stage == "Lost":
        return "Lost"
    return "Active"


crm_repository = CrmRepository()
