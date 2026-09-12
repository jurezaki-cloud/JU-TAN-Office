from __future__ import annotations

from datetime import datetime

from app.database.database import db

LINK_MODULES = (
    ("customer", "Customer"),
    ("supplier", "Supplier"),
    ("invoice", "Invoice"),
    ("offer", "Offer"),
    ("order", "Order"),
    ("purchase", "Purchase Order"),
    ("warehouse", "Warehouse Movement"),
    ("product", "Product"),
    ("crm", "CRM Activity"),
)

FILE_KINDS = ("pdf", "docx", "xlsx", "png", "jpg", "zip", "txt")


class DocumentsRepository:

    def _connect(self):
        return db.connect()

    def ensure_schema(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                name TEXT NOT NULL,
                is_folder INTEGER DEFAULT 0,
                stored_name TEXT,
                original_name TEXT,
                extension TEXT,
                kind TEXT,
                size_bytes INTEGER DEFAULT 0,
                owner TEXT,
                module TEXT,
                entity_id INTEGER,
                entity_label TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(parent_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_parent ON documents(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name)")
        conn.commit()
        conn.close()

    def get(self, document_id: int):
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id=?", (document_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def children(self, parent_id: int | None) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute(
                """
                SELECT * FROM documents
                WHERE parent_id IS NULL
                ORDER BY is_folder DESC, name COLLATE NOCASE
                """
            )
        else:
            cursor.execute(
                """
                SELECT * FROM documents
                WHERE parent_id=?
                ORDER BY is_folder DESC, name COLLATE NOCASE
                """,
                (parent_id,),
            )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def folders(self) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, parent_id, name FROM documents
            WHERE is_folder=1
            ORDER BY name COLLATE NOCASE
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def search(
        self,
        query: str = "",
        kind: str = "all",
        module: str = "all",
        owner: str = "all",
        date_from: str | None = None,
        date_to: str | None = None,
        parent_id: int | None = None,
        scoped: bool = True,
    ) -> list:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        clauses = ["1=1"]
        params: list = []
        if scoped:
            if parent_id is None:
                clauses.append("parent_id IS NULL")
            else:
                clauses.append("parent_id=?")
                params.append(parent_id)
        if query.strip():
            clauses.append("(name LIKE ? OR IFNULL(entity_label,'') LIKE ? OR IFNULL(original_name,'') LIKE ?)")
            like = f"%{query.strip()}%"
            params.extend([like, like, like])
        if kind not in ("all", "", None):
            if kind == "image":
                clauses.append("kind IN ('png','jpg')")
            else:
                clauses.append("kind=?")
                params.append(kind)
        if module not in ("all", "", None):
            clauses.append("module=?")
            params.append(module)
        if owner not in ("all", "", None):
            clauses.append("owner=?")
            params.append(owner)
        if date_from:
            clauses.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("created_at <= ?")
            params.append(date_to)
        sql = f"""
            SELECT * FROM documents
            WHERE {' AND '.join(clauses)}
            ORDER BY is_folder DESC, name COLLATE NOCASE
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def owners(self) -> list[str]:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT owner FROM documents
            WHERE IFNULL(owner,'') != ''
            ORDER BY owner COLLATE NOCASE
            """
        )
        rows = [row[0] for row in cursor.fetchall()]
        conn.close()
        return rows

    def add(self, **fields) -> int:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents(
                parent_id, name, is_folder, stored_name, original_name,
                extension, kind, size_bytes, owner, module, entity_id,
                entity_label, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                fields.get("parent_id"),
                fields["name"],
                1 if fields.get("is_folder") else 0,
                fields.get("stored_name") or "",
                fields.get("original_name") or fields["name"],
                fields.get("extension") or "",
                fields.get("kind") or "",
                int(fields.get("size_bytes") or 0),
                fields.get("owner") or "",
                fields.get("module") or "",
                fields.get("entity_id"),
                fields.get("entity_label") or "",
                now,
                now,
            ),
        )
        conn.commit()
        document_id = cursor.lastrowid
        conn.close()
        return document_id

    def update_meta(self, document_id: int, **fields) -> None:
        self.ensure_schema()
        allowed = {
            "parent_id", "name", "owner", "module", "entity_id",
            "entity_label", "stored_name", "size_bytes",
        }
        assignments = []
        values = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            assignments.append(f"{key}=?")
            values.append(value)
        if not assignments:
            return
        assignments.append("updated_at=?")
        values.append(datetime.now().isoformat(timespec="seconds"))
        values.append(document_id)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE documents SET {', '.join(assignments)} WHERE id=?",
            values,
        )
        conn.commit()
        conn.close()

    def delete(self, document_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id=?", (document_id,))
        conn.commit()
        conn.close()

    def descendants(self, folder_id: int) -> list:
        items = []
        for child in self.children(folder_id):
            items.append(child)
            if child[3]:
                items.extend(self.descendants(child[0]))
        return items

    def kpis(self) -> dict:
        self.ensure_schema()
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents WHERE is_folder=0")
        total = int(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM documents WHERE kind='pdf'")
        pdf = int(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM documents WHERE kind IN ('png','jpg')")
        images = int(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM documents WHERE kind='docx'")
        word = int(cursor.fetchone()[0])
        cursor.execute("SELECT COUNT(*) FROM documents WHERE kind='xlsx'")
        excel = int(cursor.fetchone()[0])
        cursor.execute("SELECT IFNULL(SUM(size_bytes),0) FROM documents WHERE is_folder=0")
        size = int(cursor.fetchone()[0] or 0)
        conn.close()
        return {
            "total": total,
            "pdf": pdf,
            "images": images,
            "word": word,
            "excel": excel,
            "size": size,
        }


documents_repository = DocumentsRepository()
