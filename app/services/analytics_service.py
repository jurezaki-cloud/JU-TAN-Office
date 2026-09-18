from datetime import date

from app.database.database import db


def _month_keys(count, today=None):
    current = today or date.today()
    year, month = current.year, current.month
    result = []
    for _ in range(count):
        result.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(result))


class AnalyticsService:
    def __init__(self, database=None):
        self.db = database or db

    def summary(self, today=None):
        selected = (today or date.today()).isoformat()
        year = selected[:4]
        with self.db.connect() as conn:
            customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            offers = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
            invoices = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            revenue = conn.execute(
                """SELECT COALESCE(SUM(amount), 0) FROM payments
                   WHERE substr(payment_date, 1, 4)=?""",
                (year,),
            ).fetchone()[0]
            open_amount = conn.execute(
                "SELECT COALESCE(SUM(total-paid_amount), 0) FROM invoices WHERE paid_amount < total"
            ).fetchone()[0]
            overdue_amount = conn.execute(
                """SELECT COALESCE(SUM(total-paid_amount), 0) FROM invoices
                   WHERE paid_amount < total AND due_date < ?""",
                (selected,),
            ).fetchone()[0]
            overdue_count = conn.execute(
                """SELECT COUNT(*) FROM invoices
                   WHERE paid_amount < total AND due_date < ?""",
                (selected,),
            ).fetchone()[0]
        return {
            "customers": customers, "offers": offers, "invoices": invoices,
            "revenue": float(revenue), "open_amount": float(open_amount),
            "overdue_amount": float(overdue_amount), "overdue_count": overdue_count,
        }

    def monthly_revenue(self, months=12, today=None):
        keys = _month_keys(months, today)
        with self.db.connect() as conn:
            rows = conn.execute(
                """SELECT substr(payment_date, 1, 7), SUM(amount)
                   FROM payments
                   WHERE substr(payment_date, 1, 7) BETWEEN ? AND ?
                   GROUP BY substr(payment_date, 1, 7)""",
                (keys[0], keys[-1]),
            ).fetchall()
        values = {row[0]: float(row[1]) for row in rows}
        return [(key, values.get(key, 0.0)) for key in keys]

    def receivables(self, today=None):
        selected = (today or date.today()).isoformat()
        with self.db.connect() as conn:
            rows = conn.execute(
                """SELECT i.number, c.company, i.issue_date, i.due_date,
                          i.total, i.paid_amount, i.total-i.paid_amount,
                          CASE WHEN i.due_date < ? THEN 'Zapadel' ELSE i.status END
                   FROM invoices i JOIN customers c ON c.id=i.customer_id
                   WHERE i.paid_amount < i.total
                   ORDER BY i.due_date, i.number""",
                (selected,),
            ).fetchall()
        return rows

    def top_customers(self, limit=10):
        with self.db.connect() as conn:
            return conn.execute(
                """SELECT c.company, COUNT(i.id), COALESCE(SUM(i.total), 0),
                          COALESCE(SUM(i.paid_amount), 0)
                   FROM customers c JOIN invoices i ON i.customer_id=c.id
                   GROUP BY c.id, c.company
                   ORDER BY SUM(i.total) DESC, c.company
                   LIMIT ?""",
                (limit,),
            ).fetchall()


analytics_service = AnalyticsService()
