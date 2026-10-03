"""Local, read-only business answers backed by Office repositories."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.permissions import can_open_page
from app.utils.money import format_eur


@dataclass(frozen=True)
class AssistantAnswer:
    title: str
    body: str
    page: int | None = None


def _allowed(page: int) -> bool:
    return can_open_page(page)


def answer(question: str, today: date | None = None) -> AssistantAnswer:
    """Supported intents are explicit; unknown questions never generate facts."""
    text = " ".join((question or "").casefold().split())
    now = today or date.today()
    if any(word in text for word in ("dolguje", "dolž", "neplačan")):
        if not (_allowed(1) and _allowed(2)):
            return AssistantAnswer("Računi", "Nimaš dovoljenja za vpogled v račune in stranke.")
        amount = re.search(r"(\d[\d\s.,]*)\s*€", text)
        threshold = float(amount.group(1).replace(" ", "").replace(".", "").replace(",", ".")) if amount else 0
        return _debtors(threshold)
    if "ponudb" in text and any(word in text for word in ("čaka", "cak", "odgovor", "dni")):
        if not (_allowed(3) and _allowed(2)):
            return AssistantAnswer("Ponudbe", "Nimaš dovoljenja za vpogled v ponudbe in stranke.")
        days = re.search(r"(\d+)\s*dni", text)
        return _waiting_offers(int(days.group(1)) if days else 14, now)
    if any(word in text for word in ("zaloga", "zalogo", "zalogi", "naroči")):
        if not _allowed(10):
            return AssistantAnswer("Zaloga", "Nimaš dovoljenja za vpogled v skladišče.")
        return _low_stock()
    if any(word in text for word in ("zapade", "zapadlih", "terjatev", "terjatve")):
        if not _allowed(6):
            return AssistantAnswer("Terjatve", "Nimaš dovoljenja za vpogled v plačila.")
        return _collections(now)
    if any(word in text for word in ("povzetek", "poslovanje", "promet")):
        if not _allowed(1):
            return AssistantAnswer("Poslovanje", "Nimaš dovoljenja za vpogled v račune.")
        return _summary(text, now)
    if "opomin" in text or "e-pošt" in text:
        return AssistantAnswer("Osnutek",
            "Za osnutek izberi konkreten račun v Plačilih. Pred pošiljanjem preveri naslovnika, znesek in besedilo.", 6)
    return AssistantAnswer("Podprta vprašanja",
        "Poskusi: »Kdo mi dolguje več kot 500 €?«, »Katere ponudbe čakajo več kot 14 dni?«, "
        "»Kateri artikli imajo nizko zalogo?« ali »Povzetek poslovanja ta mesec«.")


def _debtors(threshold: float) -> AssistantAnswer:
    from app.database.database import db
    conn = db.connect()
    try:
        rows = conn.execute("""
            SELECT c.company, SUM(MAX(0, i.total - COALESCE(p.paid, 0)))
            FROM invoices i JOIN customers c ON c.id=i.customer_id
            LEFT JOIN (SELECT invoice_id, SUM(amount) AS paid FROM payments GROUP BY invoice_id) p
              ON p.invoice_id=i.id
            WHERE i.status NOT IN ('Osnutek', 'Storniran')
            GROUP BY c.id, c.company
            HAVING SUM(MAX(0, i.total - COALESCE(p.paid, 0))) > ?
            ORDER BY 2 DESC LIMIT 30
        """, (threshold,)).fetchall()
    finally:
        conn.close()
    lines = [f"{name}: {format_eur(total)}" for name, total in rows]
    return AssistantAnswer("Odprte terjatve", "\n".join(lines) if lines else "Ni ustreznih odprtih terjatev.", 1)


def _waiting_offers(days: int, now: date) -> AssistantAnswer:
    from app.database.database import db
    days = max(1, min(days, 3650))
    conn = db.connect()
    try:
        rows = conn.execute("""
            SELECT o.number, c.company, o.issue_date FROM offers o
            JOIN customers c ON c.id=o.customer_id
            WHERE o.status='Poslana' AND o.issue_date < ?
            ORDER BY o.issue_date LIMIT 30
        """, ((now - timedelta(days=days)).isoformat(),)).fetchall()
    finally:
        conn.close()
    lines = [f"{number} · {name} · {issued}" for number, name, issued in rows]
    return AssistantAnswer(f"Ponudbe brez odgovora več kot {days} dni",
                           "\n".join(lines) if lines else "Ni takih ponudb.", 3)


def _low_stock() -> AssistantAnswer:
    from app.modules.warehouse.warehouse_service import WarehouseService
    rows = [row for row in WarehouseService().stock_rows()
            if row.min_qty > 0 and row.free <= row.min_qty]
    rows.sort(key=lambda row: (row.free - row.min_qty, row.name))
    lines = [f"{row.name} · {row.warehouse}: prosto {row.free:g}, minimum {row.min_qty:g}"
             for row in rows[:30]]
    return AssistantAnswer("Nizka zaloga", "\n".join(lines) if lines else
                           "Ni artiklov pod nastavljeno minimalno zalogo.", 10)


def _collections(now: date) -> AssistantAnswer:
    from app.database.database import db
    conn = db.connect()
    try:
        rows = conn.execute("""
            SELECT i.invoice_number, COALESCE(c.company, ''), i.due_date,
                   MAX(0, i.total - COALESCE(p.paid, 0)) AS remaining
            FROM invoices i
            LEFT JOIN customers c ON c.id=i.customer_id
            LEFT JOIN (SELECT invoice_id, SUM(amount) AS paid FROM payments GROUP BY invoice_id) p
              ON p.invoice_id=i.id
            WHERE i.status NOT IN ('Osnutek', 'Storniran', 'Plačan')
              AND IFNULL(i.due_date, '') != '' AND i.due_date < ?
              AND (i.total - COALESCE(p.paid, 0)) > 0.009
            ORDER BY i.due_date, remaining DESC LIMIT 30
        """, (now.isoformat(),)).fetchall()
    finally:
        conn.close()
    total = sum(float(row[3] or 0) for row in rows)
    lines = [f"{number} · {customer} · rok {due} · {format_eur(remaining)}"
             for number, customer, due, remaining in rows]
    if not lines:
        return AssistantAnswer("Zapadle terjatve", "Ni zapadlih odprtih terjatev.", 6)
    return AssistantAnswer("Zapadle terjatve",
                           f"Skupaj: {format_eur(total)}\n" + "\n".join(lines), 6)


def _summary(text: str, now: date) -> AssistantAnswer:
    from app.database.database import db
    if "danes" in text:
        start, label = now, "danes"
    elif "teden" in text:
        start, label = now - timedelta(days=now.weekday()), "ta teden"
    else:
        start, label = now.replace(day=1), "ta mesec"
    conn = db.connect()
    try:
        count, amount = conn.execute("""
            SELECT COUNT(*), COALESCE(SUM(total), 0) FROM invoices
            WHERE issue_date BETWEEN ? AND ? AND status NOT IN ('Osnutek', 'Storniran')
        """, (start.isoformat(), now.isoformat())).fetchone()
    finally:
        conn.close()
    return AssistantAnswer(f"Poslovanje {label}",
        f"Izdani računi: {count}\nZaračunano: {format_eur(amount)}\n"
        "To je znesek računov, ne prejetih plačil.", 1)
