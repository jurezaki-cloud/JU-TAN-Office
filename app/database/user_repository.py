"""SQLite users + user_permissions — multi-user authentication source of truth."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.database.database import db


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_username(username: str) -> str:
    return (username or "").strip().casefold()


class UserRepository:
    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                username_normalized TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Read Only',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_permissions (
                user_id INTEGER NOT NULL,
                permission TEXT NOT NULL,
                PRIMARY KEY (user_id, permission),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_normalized ON users(username_normalized)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id)"
        )
        conn.commit()
        conn.close()

    def count_users(self) -> int:
        self.ensure_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
            return int(row[0] if row else 0)
        finally:
            conn.close()

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        self.ensure_schema()
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT id, username, username_normalized, password_hash, role,
                       is_active, created_at, updated_at, last_login_at
                FROM users WHERE id=?
                """,
                (int(user_id),),
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        self.ensure_schema()
        key = normalize_username(username)
        if not key:
            return None
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT id, username, username_normalized, password_hash, role,
                       is_active, created_at, updated_at, last_login_at
                FROM users WHERE username_normalized=?
                """,
                (key,),
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def list_users(self) -> list[dict[str, Any]]:
        self.ensure_schema()
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT id, username, username_normalized, password_hash, role,
                       is_active, created_at, updated_at, last_login_at
                FROM users
                ORDER BY username COLLATE NOCASE
                """
            ).fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role: str,
        is_active: bool = True,
        permissions: list[str] | None = None,
    ) -> int:
        self.ensure_schema()
        display = (username or "").strip()
        key = normalize_username(display)
        if not display or not key:
            raise ValueError("Uporabniško ime je obvezno.")
        if not password_hash:
            raise ValueError("Geslo je obvezno.")
        now = _utc_now()
        with db.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users(
                        username, username_normalized, password_hash, role,
                        is_active, created_at, updated_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        display,
                        key,
                        password_hash,
                        role,
                        1 if is_active else 0,
                        now,
                        now,
                    ),
                )
            except Exception as exc:
                # UNIQUE on username_normalized
                msg = str(exc).lower()
                if "unique" in msg or "constraint" in msg:
                    raise ValueError("Uporabniško ime že obstaja.") from exc
                raise
            user_id = int(cursor.lastrowid)
            if permissions is not None:
                self._replace_permissions(cursor, user_id, permissions)
            return user_id

    def update_user(
        self,
        user_id: int,
        *,
        username: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        password_hash: str | None = None,
        permissions: list[str] | None = None,
    ) -> None:
        self.ensure_schema()
        current = self.get_by_id(user_id)
        if current is None:
            raise ValueError("Uporabnik ne obstaja.")
        display = current["username"]
        key = current["username_normalized"]
        if username is not None:
            display = username.strip()
            key = normalize_username(display)
            if not display or not key:
                raise ValueError("Uporabniško ime je obvezno.")
        new_role = role if role is not None else current["role"]
        active = current["is_active"] if is_active is None else bool(is_active)
        pwd = password_hash if password_hash is not None else current["password_hash"]
        now = _utc_now()
        with db.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET username=?, username_normalized=?, password_hash=?,
                        role=?, is_active=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        display,
                        key,
                        pwd,
                        new_role,
                        1 if active else 0,
                        now,
                        int(user_id),
                    ),
                )
            except Exception as exc:
                msg = str(exc).lower()
                if "unique" in msg or "constraint" in msg:
                    raise ValueError("Uporabniško ime že obstaja.") from exc
                raise
            if permissions is not None:
                self._replace_permissions(cursor, int(user_id), permissions)

    def set_password_hash(self, user_id: int, password_hash: str) -> None:
        self.update_user(user_id, password_hash=password_hash)

    def touch_last_login(self, user_id: int) -> None:
        self.ensure_schema()
        now = _utc_now()
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE users SET last_login_at=?, updated_at=? WHERE id=?",
                (now, now, int(user_id)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_permissions(self, user_id: int) -> list[str]:
        self.ensure_schema()
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT permission FROM user_permissions WHERE user_id=? ORDER BY permission",
                (int(user_id),),
            ).fetchall()
            return [str(r[0]) for r in rows]
        finally:
            conn.close()

    def set_permissions(self, user_id: int, permissions: list[str]) -> None:
        self.ensure_schema()
        with db.transaction() as conn:
            self._replace_permissions(conn.cursor(), int(user_id), permissions)

    def count_active_admins(self) -> int:
        """Active users who can manage users (Administrator role or users permission)."""
        self.ensure_schema()
        conn = self._connect()
        try:
            role_count = conn.execute(
                """
                SELECT COUNT(*) FROM users
                WHERE is_active=1 AND role=?
                """,
                ("Administrator",),
            ).fetchone()
            custom = conn.execute(
                """
                SELECT COUNT(DISTINCT u.id) FROM users u
                JOIN user_permissions p ON p.user_id = u.id
                WHERE u.is_active=1 AND p.permission='users' AND u.role != 'Administrator'
                """
            ).fetchone()
            return int(role_count[0] if role_count else 0) + int(custom[0] if custom else 0)
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> None:
        """Physically delete one user and their permission rows."""
        self.ensure_schema()
        with db.transaction() as conn:
            conn.execute("DELETE FROM user_permissions WHERE user_id=?", (int(user_id),))
            conn.execute("DELETE FROM users WHERE id=?", (int(user_id),))

    def delete_all_users(self) -> None:
        """Destructive — used only by FreshResetService after verified backup."""
        self.ensure_schema()
        with db.transaction() as conn:
            conn.execute("DELETE FROM user_permissions")
            conn.execute("DELETE FROM users")

    def count_audit_actor_references(self, user_id: int, username: str) -> int:
        """Count audit_log rows attributed to this user (actor username or uid tag)."""
        self.ensure_schema()
        display = (username or "").strip()
        uid = int(user_id)
        conn = self._connect()
        try:
            # Ensure table exists even on minimal test DBs.
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    username TEXT,
                    action TEXT NOT NULL,
                    detail TEXT
                )
                """
            )
            row = conn.execute(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE lower(IFNULL(username, '')) = lower(?)
                   OR IFNULL(detail, '') LIKE ?
                   OR IFNULL(detail, '') LIKE ?
                """,
                (
                    display,
                    f"[uid={uid}]%",
                    f"%[uid={uid}] %",
                ),
            ).fetchone()
            return int(row[0] if row else 0)
        finally:
            conn.close()

    @staticmethod
    def _replace_permissions(cursor, user_id: int, permissions: list[str]) -> None:
        cursor.execute("DELETE FROM user_permissions WHERE user_id=?", (user_id,))
        seen: set[str] = set()
        for raw in permissions or []:
            key = str(raw).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            cursor.execute(
                "INSERT INTO user_permissions(user_id, permission) VALUES (?,?)",
                (user_id, key),
            )

    @staticmethod
    def _row_to_dict(row) -> dict[str, Any]:
        return {
            "id": int(row[0]),
            "username": row[1],
            "username_normalized": row[2],
            "password_hash": row[3],
            "role": row[4],
            "is_active": bool(row[5]),
            "created_at": row[6],
            "updated_at": row[7],
            "last_login_at": row[8],
        }


user_repository = UserRepository()
