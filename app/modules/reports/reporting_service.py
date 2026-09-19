from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable
from app.core.cache import ttl_cache
from app.core.pagination import DEFAULT_PAGE_SIZE
from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.excel.excel_export import excel_folders, write_workbook
from app.modules.crm.crm_repository import crm_repository
from app.modules.documents.documents_repository import documents_repository
from app.modules.purchase.purchase_repository import purchase_repository
from app.modules.suppliers.suppliers_repository import suppliers_repository
from app.modules.warehouse.warehouse_service import STATUS_LOW, warehouse_service
from app.pdf.pdf_company import load_company
from app.widgets.invoices.status_badge import invoice_badge

PAGE_SIZE = DEFAULT_PAGE_SIZE

CATALOG: list[tuple[str, list[tuple[str, str]]]] = [
    ("Dashboard", [("dashboard", "Pregled")]),
    ("Sales", [
        ("sales_invoices", "Računi"),
        ("sales_trend", "Mesečni trend"),
    ]),
    ("Finance", [
        ("finance_outstanding", "Odprti računi"),
        ("finance_paid", "Plačila"),
    ]),
    ("Inventory", [
        ("inventory_stock", "Zaloga"),
        ("inventory_low", "Nizka zaloga"),
    ]),
    ("Purchase", [
        ("purchase_orders", "Nabavna naročila"),
    ]),
    ("CRM", [
        ("crm_pipeline", "Pipeline"),
    ]),
    ("Service", [
        ("service_jobs", "Servisni nalogi"),
    ]),
    ("Customers", [
        ("customers_list", "Stranke"),
    ]),
    ("Products", [
        ("products_list", "Artikli"),
        ("products_top", "Top artikli"),
    ]),
]


@dataclass
class ReportFilters:
    date_from: date | None = None
    date_to: date | None = None
    customer_id: int | str | None = None
    supplier_id: int | str | None = None
    salesperson: str = "all"
    status: str = "all"
    category: str = "all"


@dataclass
class ReportResult:
    key: str
    title: str
    headers: list[str]
    rows: list[list[Any]]
    chart: list[tuple[str, float]] = field(default_factory=list)
    chart_kind: str = "bar"
    dashboard: dict[str, Any] = field(default_factory=dict)


class ReportingService:
    def run(self, key: str, filters: ReportFilters | None = None) -> ReportResult:
        filters = filters or ReportFilters()
        handlers: dict[str, Callable[[ReportFilters], ReportResult]] = {
            "dashboard": self._dashboard,
            "sales_invoices": self._sales_invoices,
            "sales_trend": self._sales_trend,
            "finance_outstanding": self._finance_outstanding,
            "finance_paid": self._finance_paid,
            "inventory_stock": self._inventory_stock,
            "inventory_low": self._inventory_low,
            "purchase_orders": self._purchase_orders,
            "crm_pipeline": self._crm_pipeline,
            "service_jobs": self._service_jobs,
            "customers_list": self._customers,
            "products_list": self._products,
            "products_top": self._products_top,
        }
        handler = handlers.get(key, self._sales_invoices)
        return handler(filters)

    @ttl_cache(seconds=15.0)
    def filter_options(self) -> dict:
        customers = [(row[0], str(row[1])) for row in customer_repository.get_all()]
        suppliers = [(row[0], str(row[1])) for row in suppliers_repository.get_all()]
        people = crm_repository.salespeople()
        categories = sorted({
            str(row[3] or "").strip()
            for row in article_repository.get_all()
            if str(row[3] or "").strip()
        })
        statuses = ["Osnutek", "Izdan", "Plačan", "Draft", "Ordered", "Received", "Active", "Won", "Lost"]
        return {
            "customers": customers,
            "suppliers": suppliers,
            "salespeople": people,
            "categories": categories,
            "statuses": statuses,
        }

    def export_excel(self, result: ReportResult, path: Path) -> Path:
        from app.core.permissions import audit, require

        require("export")
        audit("export", Path(path).name)
        return write_workbook(path, "reports", result.headers, result.rows)

    def export_csv(self, result: ReportResult, path: Path) -> Path:
        from app.core.permissions import audit, require

        require("export")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [";".join(_csv(value) for value in result.headers)]
        for row in result.rows:
            lines.append(";".join(_csv(value) for value in row))
        path.write_text("\n".join(lines), encoding="utf-8-sig")
        audit("export", path.name)
        return path

    def export_pdf(self, result: ReportResult, path: Path) -> Path:
        from app.core.permissions import audit, require

        require("export")
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from app.pdf.pdf_styles import BORDER, FONT, FONT_BOLD, MUTED, NAVY, TABLE_HEADER, WHITE, ensure_fonts, styles

        ensure_fonts()
        look = styles()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        company = load_company()
        doc = SimpleDocTemplate(
            str(path),
            pagesize=landscape(A4),
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=result.title,
        )
        data = [result.headers] + [
            [str(cell if cell is not None else "") for cell in row]
            for row in result.rows[:200]
        ]
        if len(data) == 1:
            data.append(["Ni podatkov"] + [""] * (len(result.headers) - 1))
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
            ("BACKGROUND", (0, 1), (-1, -1), TABLE_HEADER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story = [
            Paragraph(company.name or "JU-TAN Office", look["title"]),
            Paragraph(result.title, look["label"]),
            Paragraph(date.today().isoformat(), look["body"]),
            Spacer(1, 8),
            table,
        ]
        doc.build(story)
        audit("export", path.name)
        return path

    def export_start(self, suffix: str) -> Path:
        folder = excel_folders()["export"]
        return folder / f"report.{suffix}"

    def print_html(self, result: ReportResult) -> str:
        from app.core.permissions import audit, require

        require("print")
        audit("print", result.key)
        head = "".join(f"<th>{_esc(h)}</th>" for h in result.headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>"
            for row in result.rows[:200]
        )
        return f"<h2>{_esc(result.title)}</h2><table border='1' cellspacing='0' cellpadding='6'><tr>{head}</tr>{body}</table>"

    def _invoices(self, filters: ReportFilters) -> list:
        rows = []
        for invoice in invoice_repository.get_all():
            issue = _as_date(invoice[2])
            if not _in_dates(issue, filters.date_from, filters.date_to):
                continue
            full = invoice_repository.get_by_id(invoice[0])
            customer_id = full[2] if full else None
            if filters.customer_id not in (None, "", "all") and customer_id != filters.customer_id:
                continue
            status = str(invoice[5] or "")
            if filters.status not in ("all", "", None) and status != filters.status and invoice_badge(status) != filters.status:
                continue
            rows.append(invoice)
        return rows

    def _dashboard(self, filters: ReportFilters) -> ReportResult:
        invoices = self._invoices(filters)
        billed = [row for row in invoices if str(row[5] or "") not in ("Storniran",)]
        top_customers = _aggregate(
            [(str(row[3] or "—"), _num(row[4])) for row in billed], 8
        )
        product_map: dict[str, float] = {}
        for invoice in billed:
            for item in invoice_repository.get_items(invoice[0]):
                name = str(item[3] or item[2] or "—")
                if filters.category not in ("all", "", None) and str(item[6] or "") != filters.category:
                    continue
                product_map[name] = product_map.get(name, 0) + _num(item[5])
        top_products = sorted(product_map.items(), key=lambda item: item[1], reverse=True)[:8]
        monthly: dict[str, float] = {}
        for row in billed:
            key = str(row[2] or "")[:7] or "—"
            monthly[key] = monthly.get(key, 0) + _num(row[4])
        trend = sorted(monthly.items())[-12:]
        outstanding = [
            row for row in billed
            if invoice_badge(row[5], invoice_repository.get_by_id(row[0])[4] if invoice_repository.get_by_id(row[0]) else None)
            in ("Neplačano", "Zapadlo", "Osnutek")
        ]
        low = [row for row in warehouse_service.stock_rows() if row.status == STATUS_LOW]
        try:
            docs = documents_repository.search(scoped=False)
            doc_count = sum(1 for doc in docs if not doc[3])
        except Exception:
            doc_count = 0
        offers = list(offer_repository.get_all())
        orders = list(order_repository.get_all())
        return ReportResult(
            key="dashboard",
            title="Reporting Dashboard",
            headers=["KPI", "Vrednost"],
            rows=[
                ["Računi v obdobju", len(billed)],
                ["Odprti računi", len(outstanding)],
                ["Ponudbe", len(offers)],
                ["Naročila", len(orders)],
                ["Nizka zaloga", len(low)],
                ["Dokumenti (DMS)", doc_count],
            ],
            chart=trend,
            chart_kind="line",
            dashboard={
                "top_customers": [(name, _money(value)) for name, value in top_customers],
                "top_products": [(name, f"{value:g}") for name, value in top_products],
                "monthly": trend,
                "outstanding": outstanding[:12],
                "low_stock": [(row.code, row.name, row.qty, row.min_qty) for row in low[:12]],
                "trend": trend,
            },
        )

    def _sales_invoices(self, filters: ReportFilters) -> ReportResult:
        rows = []
        chart_map: dict[str, float] = {}
        for invoice in self._invoices(filters):
            rows.append([invoice[1], invoice[3], invoice[2], invoice[5], _money(invoice[4])])
            key = str(invoice[2] or "")[:7]
            chart_map[key] = chart_map.get(key, 0) + _num(invoice[4])
        return ReportResult("sales_invoices", "Sales — Računi", ["Številka", "Stranka", "Datum", "Status", "Znesek"], rows, sorted(chart_map.items()), "bar")

    def _sales_trend(self, filters: ReportFilters) -> ReportResult:
        result = self._sales_invoices(filters)
        result.key = "sales_trend"
        result.title = "Sales — Trend"
        result.chart_kind = "line"
        return result

    def _finance_outstanding(self, filters: ReportFilters) -> ReportResult:
        rows = []
        chart_map: dict[str, float] = {}
        for invoice in self._invoices(filters):
            full = invoice_repository.get_by_id(invoice[0])
            badge = invoice_badge(invoice[5], full[4] if full else None)
            if badge not in ("Neplačano", "Zapadlo", "Osnutek"):
                continue
            rows.append([invoice[1], invoice[3], invoice[2], badge, _money(invoice[4])])
            chart_map[badge] = chart_map.get(badge, 0) + _num(invoice[4])
        return ReportResult(
            "finance_outstanding",
            "Finance — Odprti računi",
            ["Številka", "Stranka", "Datum", "Status", "Znesek"],
            rows,
            list(chart_map.items()),
            "bar",
        )

    def _finance_paid(self, filters: ReportFilters) -> ReportResult:
        rows = []
        total = 0.0
        for invoice in self._invoices(filters):
            if invoice_badge(invoice[5]) != "Plačano":
                continue
            rows.append([invoice[1], invoice[3], invoice[2], "Plačano", _money(invoice[4])])
            total += _num(invoice[4])
        return ReportResult("finance_paid", "Finance — Plačila", ["Številka", "Stranka", "Datum", "Status", "Znesek"], rows, [("Plačano", total)], "pie")

    def _inventory_stock(self, filters: ReportFilters) -> ReportResult:
        rows = []
        chart = []
        for item in warehouse_service.stock_rows():
            if filters.category not in ("all", "", None) and item.category != filters.category:
                continue
            if filters.status not in ("all", "", None) and item.status != filters.status:
                continue
            rows.append([item.code, item.name, item.warehouse, item.qty, item.free, item.status, item.category])
            chart.append((item.name[:12], float(item.qty)))
        return ReportResult("inventory_stock", "Inventory — Zaloga", ["Šifra", "Naziv", "Skladišče", "Zaloga", "Prosto", "Status", "Kategorija"], rows, chart[:12], "bar")

    def _inventory_low(self, filters: ReportFilters) -> ReportResult:
        result = self._inventory_stock(filters)
        result.rows = [row for row in result.rows if "Nizka" in str(row[5]) or "Ni zaloge" in str(row[5])]
        result.key = "inventory_low"
        result.title = "Inventory — Nizka zaloga"
        return result

    def _purchase_orders(self, filters: ReportFilters) -> ReportResult:
        rows = []
        chart_map: dict[str, float] = {}
        for row in purchase_repository.get_all():
            issue = _as_date(row[3])
            if not _in_dates(issue, filters.date_from, filters.date_to):
                continue
            if filters.supplier_id not in (None, "", "all") and row[7] != filters.supplier_id:
                continue
            if filters.status not in ("all", "", None) and row[5] != filters.status:
                continue
            rows.append([row[1], row[2], row[3], row[5], _money(row[6])])
            chart_map[str(row[2] or "—")] = chart_map.get(str(row[2] or "—"), 0) + _num(row[6])
        return ReportResult("purchase_orders", "Purchase — Naročila", ["Številka", "Dobavitelj", "Datum", "Status", "Znesek"], rows, list(chart_map.items())[:12], "bar")

    def _crm_pipeline(self, filters: ReportFilters) -> ReportResult:
        rows = []
        chart_map: dict[str, float] = {}
        for deal in crm_repository.deals():
            created = _as_date(str(deal[10] or "")[:10])
            if not _in_dates(created, filters.date_from, filters.date_to):
                continue
            if filters.salesperson not in ("all", "", None) and deal[6] != filters.salesperson:
                continue
            if filters.status not in ("all", "", None) and deal[9] != filters.status and deal[5] != filters.status:
                continue
            if filters.customer_id not in (None, "", "all") and deal[1] != filters.customer_id:
                continue
            rows.append([deal[3], deal[4], deal[5], deal[9], deal[6], deal[7], _money(deal[8])])
            chart_map[str(deal[5])] = chart_map.get(str(deal[5]), 0) + 1
        return ReportResult("crm_pipeline", "CRM — Pipeline", ["Naslov", "Podjetje", "Stage", "Status", "Skrbnik", "Prioriteta", "Vrednost"], rows, list(chart_map.items()), "pie")

    def _service_jobs(self, filters: ReportFilters) -> ReportResult:
        try:
            from app.modules.service import service_repository  # type: ignore
            rows = [[job[1], job[2], job[3]] for job in service_repository.get_all()]
        except Exception:
            rows = []
        return ReportResult(
            "service_jobs",
            "Service",
            ["Nalog", "Stranka", "Status"],
            rows or [["Modul Service še ni na voljo", "—", "—"]],
            [],
            "none",
        )

    def _customers(self, filters: ReportFilters) -> ReportResult:
        rows = []
        for customer in customer_repository.get_all():
            full = customer_repository.get_by_id(customer[0])
            if full is None:
                continue
            if filters.customer_id not in (None, "", "all") and customer[0] != filters.customer_id:
                continue
            rows.append([full[1], full[2], full[8], full[9], full[7], full[5]])
        return ReportResult("customers_list", "Customers", ["Naziv", "Kontakt", "Email", "Telefon", "Davčna", "Kraj"], rows, [], "none")

    def _products(self, filters: ReportFilters) -> ReportResult:
        rows = []
        for article in article_repository.get_all():
            if filters.category not in ("all", "", None) and str(article[3] or "") != filters.category:
                continue
            rows.append([article[1], article[2], article[3], article[4], article[5]])
        return ReportResult("products_list", "Products", ["Šifra", "Naziv", "Kategorija", "Cena", "DDV"], rows, [], "none")

    def _products_top(self, filters: ReportFilters) -> ReportResult:
        dash = self._dashboard(filters)
        rows = [[name, qty] for name, qty in dash.dashboard.get("top_products") or []]
        chart = [(name, float(str(qty).replace(",", ".").split()[0] or 0)) for name, qty in rows]
        return ReportResult("products_top", "Products — Top", ["Artikel", "Količina"], rows, chart, "bar")


def _num(value) -> float:
    try:
        if isinstance(value, str):
            value = value.replace(" ", "").replace("€", "").replace(",", ".")
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _money(value) -> str:
    return f"{_num(value):,.2f} €".replace(",", " ")


def _as_date(value) -> date | None:
    text = str(value or "")[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _in_dates(value: date | None, start: date | None, end: date | None) -> bool:
    if value is None:
        return start is None and end is None
    if start and value < start:
        return False
    if end and value > end:
        return False
    return True


def _aggregate(pairs: list[tuple[str, float]], limit: int) -> list[tuple[str, float]]:
    grouped: dict[str, float] = {}
    for name, value in pairs:
        grouped[name] = grouped.get(name, 0) + value
    return sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:limit]


def _csv(value) -> str:
    text = str(value if value is not None else "")
    if ";" in text or '"' in text:
        return '"' + text.replace('"', '""') + '"'
    return text


def _esc(value) -> str:
    return str(value if value is not None else "").replace("&", "&amp;").replace("<", "&lt;")


reporting_service = ReportingService()
