"""SQLite persistenca za Automation Engine."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.database.database import db

TRIGGERS = (
    ("invoice_created", "Invoice Created"),
    ("invoice_paid", "Invoice Paid"),
    ("invoice_overdue", "Invoice Overdue"),
    ("offer_accepted", "Offer Accepted"),
    ("customer_created", "Customer Created"),
    ("order_completed", "Order Completed"),
    ("purchase_received", "Purchase Received"),
    ("stock_below_minimum", "Stock Below Minimum"),
    ("crm_lead_won", "CRM Lead Won"),
    ("crm_lead_lost", "CRM Lead Lost"),
    ("manual", "Manual Trigger"),
    ("scheduled", "Scheduled Trigger"),
)

CONDITION_FIELDS = (
    ("invoice_total", "Invoice Total"),
    ("customer_category", "Customer Category"),
    ("warehouse", "Warehouse"),
    ("product_category", "Product Category"),
    ("country", "Country"),
    ("payment_method", "Payment Method"),
    ("custom_expression", "Custom Expression"),
)

OPERATORS = (
    ("gt", ">"),
    ("gte", "≥"),
    ("lt", "<"),
    ("lte", "≤"),
    ("eq", "="),
    ("ne", "≠"),
    ("contains", "vsebuje"),
)

ACTIONS = (
    ("create_invoice", "Create Invoice"),
    ("create_purchase_order", "Create Purchase Order"),
    ("create_crm_activity", "Create CRM Activity"),
    ("create_reminder", "Create Reminder"),
    ("reserve_inventory", "Reserve Inventory"),
    ("update_status", "Update Status"),
    ("generate_pdf", "Generate PDF"),
    ("send_email", "Send Email"),
    ("send_notification", "Send Notification"),
    ("archive_document", "Archive Document"),
    ("python_hook", "Execute Python Hook"),
)

SCHEDULE_KINDS = (
    ("none", "Brez"),
    ("manual", "Manual Run"),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("cron", "Cron Expression"),
)

TRIGGER_LABELS = dict(TRIGGERS)
ACTION_LABELS = dict(ACTIONS)


class AutomationRepository:
    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                trigger_key TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                schedule_kind TEXT DEFAULT 'none',
                schedule_value TEXT,
                last_run_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_rule_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                join_op TEXT DEFAULT 'AND',
                negate INTEGER DEFAULT 0,
                field TEXT NOT NULL,
                operator TEXT DEFAULT 'eq',
                value TEXT,
                FOREIGN KEY(rule_id) REFERENCES automation_rules(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_rule_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0,
                action_key TEXT NOT NULL,
                config_json TEXT,
                FOREIGN KEY(rule_id) REFERENCES automation_rules(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER,
                rule_name TEXT,
                trigger_key TEXT,
                fingerprint TEXT,
                started_at TEXT,
                ended_at TEXT,
                duration_ms INTEGER,
                result TEXT,
                user_name TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                context_json TEXT
            )
        """)
        conn.commit()
        conn.close()

    def list_rules(self, query: str = "", trigger: str = "all", enabled: str = "all") -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        clauses = ["1=1"]
        params: list[Any] = []
        if query.strip():
            clauses.append("(name LIKE ? OR IFNULL(description,'') LIKE ? OR trigger_key LIKE ?)")
            like = f"%{query.strip()}%"
            params.extend([like, like, like])
        if trigger not in ("all", "", None):
            clauses.append("trigger_key=?")
            params.append(trigger)
        if enabled == "on":
            clauses.append("enabled=1")
        elif enabled == "off":
            clauses.append("enabled=0")
        cursor.execute(
            f"""
            SELECT id, name, trigger_key, enabled, priority, schedule_kind,
                   schedule_value, last_run_at, description
            FROM automation_rules
            WHERE {' AND '.join(clauses)}
            ORDER BY priority ASC, id ASC
            """,
            params,
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_rule(self, rule_id: int) -> dict | None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM automation_rules WHERE id=?", (rule_id,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return None
        cursor.execute(
            """
            SELECT id, sort_order, join_op, negate, field, operator, value
            FROM automation_rule_conditions
            WHERE rule_id=? ORDER BY sort_order, id
            """,
            (rule_id,),
        )
        conditions = cursor.fetchall()
        cursor.execute(
            """
            SELECT id, sort_order, action_key, config_json
            FROM automation_rule_actions
            WHERE rule_id=? ORDER BY sort_order, id
            """,
            (rule_id,),
        )
        actions = cursor.fetchall()
        conn.close()
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2] or "",
            "trigger_key": row[3],
            "enabled": bool(row[4]),
            "priority": int(row[5] or 100),
            "schedule_kind": row[6] or "none",
            "schedule_value": row[7] or "",
            "last_run_at": row[8],
            "conditions": [
                {
                    "id": item[0],
                    "sort_order": item[1],
                    "join_op": item[2] or "AND",
                    "negate": bool(item[3]),
                    "field": item[4],
                    "operator": item[5] or "eq",
                    "value": item[6] or "",
                }
                for item in conditions
            ],
            "actions": [
                {
                    "id": item[0],
                    "sort_order": item[1],
                    "action_key": item[2],
                    "config": json.loads(item[3] or "{}"),
                }
                for item in actions
            ],
        }

    def save_rule(self, data: dict) -> int:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        conn = self._connect()
        cursor = conn.cursor()
        rule_id = data.get("id")
        values = (
            data.get("name") or "Pravilo",
            data.get("description") or "",
            data.get("trigger_key") or "manual",
            1 if data.get("enabled", True) else 0,
            int(data.get("priority") or 100),
            data.get("schedule_kind") or "none",
            data.get("schedule_value") or "",
            now,
        )
        if rule_id:
            cursor.execute(
                """
                UPDATE automation_rules
                SET name=?, description=?, trigger_key=?, enabled=?, priority=?,
                    schedule_kind=?, schedule_value=?, updated_at=?
                WHERE id=?
                """,
                (*values, rule_id),
            )
            cursor.execute("DELETE FROM automation_rule_conditions WHERE rule_id=?", (rule_id,))
            cursor.execute("DELETE FROM automation_rule_actions WHERE rule_id=?", (rule_id,))
        else:
            cursor.execute(
                """
                INSERT INTO automation_rules(
                    name, description, trigger_key, enabled, priority,
                    schedule_kind, schedule_value, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (*values, now),
            )
            rule_id = cursor.lastrowid
        for index, cond in enumerate(data.get("conditions") or []):
            cursor.execute(
                """
                INSERT INTO automation_rule_conditions(
                    rule_id, sort_order, join_op, negate, field, operator, value
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    rule_id,
                    index,
                    cond.get("join_op") or "AND",
                    1 if cond.get("negate") else 0,
                    cond.get("field") or "invoice_total",
                    cond.get("operator") or "eq",
                    str(cond.get("value") or ""),
                ),
            )
        for index, action in enumerate(data.get("actions") or []):
            cursor.execute(
                """
                INSERT INTO automation_rule_actions(
                    rule_id, sort_order, action_key, config_json
                ) VALUES (?,?,?,?)
                """,
                (
                    rule_id,
                    index,
                    action.get("action_key") or "send_notification",
                    json.dumps(action.get("config") or {}, ensure_ascii=False),
                ),
            )
        conn.commit()
        conn.close()
        return int(rule_id)

    def delete_rule(self, rule_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM automation_rule_conditions WHERE rule_id=?", (rule_id,))
        cursor.execute("DELETE FROM automation_rule_actions WHERE rule_id=?", (rule_id,))
        cursor.execute("DELETE FROM automation_rules WHERE id=?", (rule_id,))
        conn.commit()
        conn.close()

    def set_enabled(self, rule_id: int, enabled: bool) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE automation_rules SET enabled=?, updated_at=? WHERE id=?",
            (1 if enabled else 0, datetime.now().isoformat(timespec="seconds"), rule_id),
        )
        conn.commit()
        conn.close()

    def mark_run(self, rule_id: int, when: str) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE automation_rules SET last_run_at=?, updated_at=? WHERE id=?",
            (when, when, rule_id),
        )
        conn.commit()
        conn.close()

    def add_log(self, payload: dict) -> int:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO automation_execution_log(
                rule_id, rule_name, trigger_key, fingerprint, started_at, ended_at,
                duration_ms, result, user_name, error_message, retry_count, context_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                payload.get("rule_id"),
                payload.get("rule_name") or "",
                payload.get("trigger_key") or "",
                payload.get("fingerprint") or "",
                payload.get("started_at"),
                payload.get("ended_at"),
                int(payload.get("duration_ms") or 0),
                payload.get("result") or "success",
                payload.get("user_name") or "",
                payload.get("error_message") or "",
                int(payload.get("retry_count") or 0),
                json.dumps(payload.get("context") or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return int(log_id)

    def list_logs(
        self,
        query: str = "",
        result: str = "all",
        limit: int = 200,
    ) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        clauses = ["1=1"]
        params: list[Any] = []
        if query.strip():
            clauses.append(
                "(IFNULL(rule_name,'') LIKE ? OR IFNULL(trigger_key,'') LIKE ? OR IFNULL(error_message,'') LIKE ?)"
            )
            like = f"%{query.strip()}%"
            params.extend([like, like, like])
        if result not in ("all", "", None):
            clauses.append("result=?")
            params.append(result)
        params.append(int(limit))
        cursor.execute(
            f"""
            SELECT id, rule_name, trigger_key, started_at, ended_at, duration_ms,
                   result, user_name, error_message, retry_count
            FROM automation_execution_log
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC
            LIMIT ?
            """,
            params,
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def logged_today(self, rule_id: int, fingerprint: str, day: str) -> bool:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM automation_execution_log
            WHERE rule_id=? AND fingerprint=? AND result='success'
              AND started_at LIKE ?
            LIMIT 1
            """,
            (rule_id, fingerprint, f"{day}%"),
        )
        found = cursor.fetchone() is not None
        conn.close()
        return found

    def kpis(self) -> dict:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END) FROM automation_rules")
        total, enabled = cursor.fetchone()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN result='failed' THEN 1 ELSE 0 END)
            FROM automation_execution_log WHERE started_at LIKE ?
            """,
            (f"{today}%",),
        )
        runs, failed = cursor.fetchone()
        conn.close()
        return {
            "rules": int(total or 0),
            "enabled": int(enabled or 0),
            "runs_today": int(runs or 0),
            "failed_today": int(failed or 0),
        }


automation_repository = AutomationRepository()
