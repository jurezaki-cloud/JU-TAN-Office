"""Read-only dashboard insights; issued invoices only for sales figures."""
from __future__ import annotations

from datetime import date, timedelta

from app.core.permissions import can_open_page
from app.database.database import db
from app.utils.money import format_eur


def load_insights(today: date | None = None) -> dict[str, object]:
    today = today or date.today()
    start = today.replace(month=1, day=1)
    previous_start = start.replace(year=start.year - 1)
    try:
        previous_end = today.replace(year=today.year - 1)
    except ValueError:  # 29 February compared to 28 February.
        previous_end = today.replace(year=today.year - 1, day=28)
    result: dict[str, object] = {
        "comparison": "", "customers": [], "articles": [], "alerts": []
    }
    conn = db.connect()
    try:
        if can_open_page(1):
            sales = conn.execute("""SELECT
                COALESCE(SUM(CASE WHEN issue_date BETWEEN ? AND ? THEN total ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN issue_date BETWEEN ? AND ? THEN total ELSE 0 END), 0)
                FROM invoices WHERE status NOT IN ('Osnutek', 'Storniran')""",
                (start.isoformat(), today.isoformat(), previous_start.isoformat(),
                 previous_end.isoformat())).fetchone()
            current, previous = float(sales[0] or 0), float(sales[1] or 0)
            delta = f"{(current / previous - 1) * 100:+.1f} %" if previous else "—"
            result["comparison"] = (
                f"Izdani računi letos: {format_eur(current)} · lani do istega dne: "
                f"{format_eur(previous)} · sprememba: {delta}"
            )
        if can_open_page(1) and can_open_page(2):
            result["customers"] = conn.execute("""
                SELECT c.company, SUM(i.total) FROM invoices i
                JOIN customers c ON c.id=i.customer_id
                WHERE i.status NOT IN ('Osnutek', 'Storniran')
                  AND i.issue_date BETWEEN ? AND ?
                GROUP BY c.id ORDER BY SUM(i.total) DESC LIMIT 5
            """, (start.isoformat(), today.isoformat())).fetchall()
        if can_open_page(1) and can_open_page(4):
            result["articles"] = conn.execute("""
                SELECT COALESCE(NULLIF(item.name, ''), item.code, 'Artikel'),
                       SUM(item.total) FROM invoice_items item
                JOIN invoices i ON i.id=item.invoice_id
                WHERE i.status NOT IN ('Osnutek', 'Storniran')
                  AND i.issue_date BETWEEN ? AND ?
                GROUP BY COALESCE(NULLIF(item.name, ''), item.code, 'Artikel')
                ORDER BY SUM(item.total) DESC LIMIT 5
            """, (start.isoformat(), today.isoformat())).fetchall()
        if can_open_page(6):
            overdue_count = conn.execute("""SELECT COUNT(*) FROM invoices
                WHERE status NOT IN ('Osnutek', 'Storniran', 'Plačan')
                  AND IFNULL(due_date, '') != '' AND due_date < ?""",
                (today.isoformat(),)).fetchone()[0]
            if overdue_count:
                result["alerts"].append((6, f"{overdue_count} zapadlih računov zahteva pozornost"))
        if can_open_page(3):
            count = conn.execute("""SELECT COUNT(*) FROM offers
                WHERE status='Poslana' AND issue_date < ?""",
                ((today - timedelta(days=14)).isoformat(),)).fetchone()[0]
            if count:
                result["alerts"].append((3, f"{count} ponudb čaka več kot 14 dni"))
        if can_open_page(14) and conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crm_activities'"
        ).fetchone():
            count = conn.execute("""SELECT COUNT(*) FROM crm_activities
                WHERE is_done=0 AND due_date < ?""", (today.isoformat(),)).fetchone()[0]
            if count:
                result["alerts"].append((14, f"{count} zapadlih CRM nalog"))
            today_count = conn.execute("""SELECT COUNT(*) FROM crm_activities
                WHERE is_done=0 AND due_date = ?""", (today.isoformat(),)).fetchone()[0]
            if today_count:
                result["alerts"].append((14, f"{today_count} CRM nalog za danes"))
            upcoming = conn.execute("""SELECT COUNT(*) FROM crm_activities
                WHERE is_done=0 AND due_date > ? AND due_date <= ?""",
                (today.isoformat(), (today + timedelta(days=7)).isoformat())).fetchone()[0]
            if upcoming:
                result["alerts"].append((14, f"{upcoming} CRM nalog v naslednjih 7 dneh"))
    finally:
        conn.close()
    if can_open_page(10):
        from app.modules.warehouse.warehouse_service import WarehouseService
        count = int(WarehouseService().kpis()["low_stock"])
        if count:
            result["alerts"].append((10, f"{count} artiklov z nizko zalogo"))
    return result
