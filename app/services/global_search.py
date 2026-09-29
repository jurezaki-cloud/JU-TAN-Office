"""Read-only, permission-aware search across Office records."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.permissions import can_open_page
from app.database.database import db


@dataclass(frozen=True)
class SearchHit:
    page: int
    kind: str
    record_id: int
    title: str
    detail: str
    query: str


# Only explicitly supported tables and columns may be interpolated into SQL.
SOURCES = (
    (2, "Stranka", "customers", "company", ("company", "contact", "email", "tax_number")),
    (1, "Račun", "invoices", "invoice_number", ("invoice_number",)),
    (3, "Ponudba", "offers", "number", ("number",)),
    (4, "Artikel", "articles", "name", ("name", "code", "description")),
    (9, "Naročilo", "orders", "number", ("number",)),
    (18, "Predračun", "proformas", "number", ("number",)),
    (14, "Priložnost", "crm_pipeline", "title", ("title", "company")),
)


def search_records(query: str, limit: int = 30) -> list[SearchHit]:
    """Return matching records without changing data or exposing restricted pages."""
    query = " ".join((query or "").split())[:120]
    if len(query) < 2:
        return []
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    hits: list[SearchHit] = []
    conn = db.connect()
    try:
        for page, kind, table, title, fields in SOURCES:
            if not can_open_page(page):
                continue
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if not {"id", title}.issubset(columns):
                continue
            searchable = tuple(field for field in fields if field in columns)
            if not searchable:
                continue
            predicate = " OR ".join(f"{field} LIKE ? ESCAPE '\\'" for field in searchable)
            sql = f"SELECT id, {title} FROM {table} WHERE {predicate} ORDER BY id DESC LIMIT ?"
            rows = conn.execute(sql, (*([pattern] * len(searchable)), min(limit, 30))).fetchall()
            for record_id, value in rows:
                hits.append(SearchHit(page, kind, record_id, str(value or ""),
                                      f"{kind} · #{record_id}", query))
            if len(hits) >= limit:
                break
    finally:
        conn.close()
    return hits[:limit]
