from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.database.invoice_repository import invoice_repository

EXPORT_NOTICE = "Funkcija bo na voljo v naslednji različici"

SLO_MONTHS = (
    "jan", "feb", "mar", "apr", "maj", "jun",
    "jul", "avg", "sep", "okt", "nov", "dec",
)

MOCK_CUSTOMERS = [
    ("Acme d.o.o.", 18420.00),
    ("Nordic Trade", 15210.50),
    ("Alpska pot", 12880.00),
    ("Sava Logistics", 11140.20),
    ("Kranj Steel", 9800.00),
    ("Adria Print", 8640.80),
    ("Ljubljana Tech", 7420.00),
    ("Maribor Shop", 6310.40),
    ("Celje Group", 5180.00),
    ("Koper Marine", 4090.60),
]

MOCK_ARTICLES = [
    ("Svetilka LED 24W", 312),
    ("Kabel 3x1.5 mm", 286),
    ("Stikalo 10A", 241),
    ("Vtičnica 16A", 198),
    ("LED panel 60x60", 176),
    ("Varovalka 16A", 154),
    ("Razdelilnik 8x", 132),
    ("Nosilec DIN", 118),
    ("Spojka IP65", 97),
    ("Ohišje 24M", 84),
]


@dataclass
class AnalyticsSnapshot:
    period: str
    date_from: date
    date_to: date
    today_revenue: float
    month_revenue: float
    invoice_count: int
    active_customers: int
    line_points: list[tuple[str, float]] = field(default_factory=list)
    bar_points: list[tuple[str, float]] = field(default_factory=list)
    status_slices: list[tuple[str, float]] = field(default_factory=list)
    top_customers: list[tuple[str, float]] = field(default_factory=list)
    top_articles: list[tuple[str, float]] = field(default_factory=list)
    mock_charts: bool = False
    mock_status: bool = False
    mock_customers: bool = False
    mock_articles: bool = False


class AnalyticsController:
    """Zbere KPI in grafe iz obstoječih repository metod, brez sprememb baze."""

    def snapshot(
        self,
        period: str = "month",
        custom_from: date | None = None,
        custom_to: date | None = None,
    ) -> AnalyticsSnapshot:
        today = date.today()
        date_from, date_to = self._range(period, custom_from, custom_to, today)
        invoices = list(invoice_repository.get_all())
        in_period = [row for row in invoices if self._in_range(row, date_from, date_to)]
        billed = [row for row in in_period if not self._cancelled(row)]

        today_revenue = sum(
            self._total(row)
            for row in invoices
            if not self._cancelled(row) and self._issue_date(row) == today
        )
        month_start = today.replace(day=1)
        month_revenue = sum(
            self._total(row)
            for row in invoices
            if not self._cancelled(row)
            and self._issue_date(row) is not None
            and month_start <= self._issue_date(row) <= today
        )

        companies = {
            str(row[3]).strip()
            for row in billed
            if len(row) > 3 and row[3]
        }

        line_points, mock_charts = self._trend(invoices, date_from, date_to)
        bar_points = list(line_points)
        status_slices = self._status_slices(in_period)
        mock_status = False
        if not status_slices:
            status_slices = [
                ("Plačano", 42),
                ("Neplačano", 18),
                ("Osnutek", 9),
                ("Zapadlo", 7),
                ("Stornirano", 3),
            ]
            mock_status = True

        top_customers, mock_customers = self._top_customers(billed)
        top_articles, mock_articles = self._top_articles(billed)

        return AnalyticsSnapshot(
            period=period,
            date_from=date_from,
            date_to=date_to,
            today_revenue=today_revenue,
            month_revenue=month_revenue,
            invoice_count=len(billed),
            active_customers=len(companies),
            line_points=line_points,
            bar_points=bar_points,
            status_slices=status_slices,
            top_customers=top_customers,
            top_articles=top_articles,
            mock_charts=mock_charts,
            mock_status=mock_status,
            mock_customers=mock_customers,
            mock_articles=mock_articles,
        )

    def export_notice(self) -> str:
        return EXPORT_NOTICE

    def _range(
        self,
        period: str,
        custom_from: date | None,
        custom_to: date | None,
        today: date,
    ) -> tuple[date, date]:
        if period == "day":
            return today, today
        if period == "week":
            return today - timedelta(days=6), today
        if period == "month":
            return today.replace(day=1), today
        if period == "year":
            return today.replace(month=1, day=1), today
        start = custom_from or (today - timedelta(days=29))
        end = custom_to or today
        if start > end:
            start, end = end, start
        return start, end

    def _trend(
        self,
        invoices: list,
        date_from: date,
        date_to: date,
    ) -> tuple[list[tuple[str, float]], bool]:
        span = (date_to - date_from).days
        if span <= 45:
            points = []
            cursor = date_from
            while cursor <= date_to:
                total = sum(
                    self._total(row)
                    for row in invoices
                    if not self._cancelled(row) and self._issue_date(row) == cursor
                )
                points.append((f"{cursor.day}.", total))
                cursor += timedelta(days=1)
        else:
            points = []
            year, month = date_from.year, date_from.month
            while (year, month) <= (date_to.year, date_to.month):
                key = f"{year:04d}-{month:02d}"
                total = sum(
                    self._total(row)
                    for row in invoices
                    if not self._cancelled(row)
                    and self._issue_date(row) is not None
                    and self._issue_date(row).strftime("%Y-%m") == key
                )
                points.append((SLO_MONTHS[month - 1], total))
                month += 1
                if month > 12:
                    month = 1
                    year += 1

        if not any(value for _, value in points):
            return self._mock_points(points), True
        return points, False

    def _mock_points(self, labels: list[tuple[str, float]]) -> list[tuple[str, float]]:
        sample = [4200, 5100, 4800, 6400, 5900, 7200, 6900, 8100, 7600, 8800, 8400, 9200]
        if not labels:
            month = date.today().month
            names = [SLO_MONTHS[(month - 6 + i) % 12] for i in range(6)]
            return list(zip(names, sample[:6]))
        return [
            (label, sample[index % len(sample)])
            for index, (label, _) in enumerate(labels)
        ]

    def _status_slices(self, invoices: list) -> list[tuple[str, float]]:
        counts: dict[str, float] = {}
        for row in invoices:
            status = str(row[5] if len(row) > 5 and row[5] else "Osnutek")
            counts[status] = counts.get(status, 0) + 1
        return [(name, value) for name, value in counts.items() if value]

    def _top_customers(
        self,
        invoices: list,
    ) -> tuple[list[tuple[str, float]], bool]:
        totals: dict[str, float] = {}
        for row in invoices:
            name = str(row[3] if len(row) > 3 and row[3] else "Neznana stranka")
            totals[name] = totals.get(name, 0.0) + self._total(row)
        ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
        if ranked:
            return ranked, False
        existing = list(invoice_repository.get_customer_revenue() or [])
        if existing:
            return [(str(row[0]), float(row[2] or 0)) for row in existing[:10]], False
        return MOCK_CUSTOMERS, True

    def _top_articles(
        self,
        invoices: list,
    ) -> tuple[list[tuple[str, float]], bool]:
        totals: dict[str, float] = {}
        for row in invoices:
            invoice_id = row[0]
            for item in invoice_repository.get_items(invoice_id):
                name = str(item[3] or item[2] or "Artikel")
                qty = float(item[5] or 0)
                totals[name] = totals.get(name, 0.0) + qty
        ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
        if ranked:
            return ranked, False
        return MOCK_ARTICLES, True

    @staticmethod
    def _issue_date(row) -> date | None:
        if len(row) < 3 or not row[2]:
            return None
        try:
            return date.fromisoformat(str(row[2])[:10])
        except ValueError:
            return None

    @staticmethod
    def _total(row) -> float:
        try:
            return float(row[4] or 0)
        except (TypeError, ValueError, IndexError):
            return 0.0

    @staticmethod
    def _cancelled(row) -> bool:
        status = str(row[5] if len(row) > 5 else "")
        return status in ("Storniran", "Stornirano")

    def _in_range(self, row, date_from: date, date_to: date) -> bool:
        issued = self._issue_date(row)
        if issued is None:
            return False
        return date_from <= issued <= date_to
