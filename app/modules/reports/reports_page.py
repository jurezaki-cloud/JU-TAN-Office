from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.notify import toast
from app.modules.analytics.analytics_widgets import BarChart, LineChart, RankingTable
from app.modules.reports.reporting_service import CATALOG, ReportResult
from app.modules.reports.reports_controller import ReportsController
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.reports.report_catalog import ReportCatalog
from app.widgets.reports.report_filters import ReportFiltersBar
from app.widgets.reports.report_table import ReportTable
from app.widgets.reports.report_toolbar import ReportToolbar


class ReportsPage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ReportsPage")
        self.controller = ReportsController()
        self._key = "dashboard"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Reports")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.hide()

        self.actions = ReportToolbar()
        layout.addWidget(self.actions)
        self.filters = ReportFiltersBar()
        layout.addWidget(self.filters)

        self.catalog = ReportCatalog(CATALOG)
        self.table = ReportTable()
        self.line = LineChart()
        self.bar = BarChart()
        self.chart_stack = QStackedWidget()
        self.chart_stack.addWidget(self.bar)
        self.chart_stack.addWidget(self.line)
        empty_chart = QLabel("Ni grafa za to poročilo")
        empty_chart.setObjectName("KpiHint")
        self.chart_stack.addWidget(empty_chart)

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)
        chart_card = EnterpriseCard("DashboardCard")
        heading = QLabel("Chart")
        heading.setObjectName("SectionTitle")
        chart_card.body.addWidget(heading)
        chart_card.body.addWidget(self.chart_stack, 1)

        self.detail = QSplitter()
        self.detail.addWidget(table_card)
        self.detail.addWidget(chart_card)
        self.detail.setSizes([720, 420])

        self.dashboard = self._build_dashboard()
        self.content = QStackedWidget()
        self.content.addWidget(self.dashboard)
        self.content.addWidget(self.detail)

        split = QSplitter()
        split.setObjectName("ReportsSplitter")
        split.addWidget(self.catalog)
        split.addWidget(self.content)
        split.setSizes([220, 980])
        layout.addWidget(split, 1)

        self.status = QLabel("Pripravljeno")
        self.status.setObjectName("CustomerStatusLabel")
        layout.addWidget(self.status)

        self.actions.refresh_clicked.connect(self.reload)
        self.actions.pdf_clicked.connect(self.export_pdf)
        self.actions.excel_clicked.connect(self.export_excel)
        self.actions.csv_clicked.connect(self.export_csv)
        self.actions.print_clicked.connect(self.print_report)
        self.actions.more_clicked.connect(self.load_more)
        self.filters.filter_changed.connect(self.reload)
        self.catalog.report_chosen.connect(self._choose)
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.reports", splitters=[split, self.detail], tables=[self.table])
        QTimer.singleShot(0, self._lazy_start)

    def _build_dashboard(self) -> QWidget:
        wrap = QWidget()
        grid = QGridLayout(wrap)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(16)
        self.kpi_outstanding = KpiCard("Outstanding Invoices", "0", "Odprti računi")
        self.kpi_low = KpiCard("Low Stock", "0", "Pod pragom")
        self.top_customers = RankingTable(("Stranka", "Promet"))
        self.top_products = RankingTable(("Artikel", "Količina"))
        self.trend = LineChart()
        self.monthly = BarChart()
        cust_card = EnterpriseCard("DashboardCard")
        t1 = QLabel("Top Customers")
        t1.setObjectName("SectionTitle")
        cust_card.body.addWidget(t1)
        cust_card.body.addWidget(self.top_customers)
        prod_card = EnterpriseCard("DashboardCard")
        t2 = QLabel("Top Products")
        t2.setObjectName("SectionTitle")
        prod_card.body.addWidget(t2)
        prod_card.body.addWidget(self.top_products)
        trend_card = EnterpriseCard("DashboardCard")
        t3 = QLabel("Sales Trend")
        t3.setObjectName("SectionTitle")
        trend_card.body.addWidget(t3)
        trend_card.body.addWidget(self.trend, 1)
        month_card = EnterpriseCard("DashboardCard")
        t4 = QLabel("Monthly Revenue")
        t4.setObjectName("SectionTitle")
        month_card.body.addWidget(t4)
        month_card.body.addWidget(self.monthly, 1)
        grid.addWidget(self.kpi_outstanding, 0, 0)
        grid.addWidget(self.kpi_low, 0, 1)
        grid.addWidget(trend_card, 1, 0, 1, 2)
        grid.addWidget(month_card, 2, 0)
        grid.addWidget(cust_card, 2, 1)
        grid.addWidget(prod_card, 3, 0, 1, 2)
        return wrap

    def _lazy_start(self) -> None:
        self.filters.fill(self.controller.options())
        self.reload()

    def refresh(self) -> None:
        self.reload()

    def _choose(self, key: str) -> None:
        self._key = key
        self.reload()

    def _filters(self):
        return self.controller.filters_from(
            self.filters.date_from.date(),
            self.filters.date_to.date(),
            self.filters.customer.currentData(),
            self.filters.supplier.currentData(),
            self.filters.salesperson.currentData() or "all",
            self.filters.status.currentData() or "all",
            self.filters.category.currentData() or "all",
        )

    def reload(self) -> None:
        self.status.setText("Nalaganje…")
        self.controller.load(self._key, self._filters(), self._on_loaded, self._on_error, self)

    def _on_loaded(self, result: ReportResult) -> None:
        self._apply(result)

    def _on_error(self, message: str) -> None:
        self.status.setText(message)
        QMessageBox.warning(self, "Reports", message)

    def _apply(self, result: ReportResult) -> None:
        if result.key == "dashboard":
            self.content.setCurrentIndex(0)
            dash = result.dashboard
            self.top_customers.set_rows(dash.get("top_customers") or [])
            self.top_products.set_rows(dash.get("top_products") or [])
            self.trend.set_points(dash.get("trend") or [])
            self.monthly.set_points(dash.get("monthly") or [])
            self.kpi_outstanding.set_value(str(len(dash.get("outstanding") or [])))
            self.kpi_low.set_value(str(len(dash.get("low_stock") or [])))
        else:
            self.content.setCurrentIndex(1)
            self.table.set_report(result.headers, self.controller.visible_rows())
            if result.chart_kind == "line":
                self.line.set_points(result.chart)
                self.chart_stack.setCurrentIndex(1)
            elif result.chart_kind == "none" or not result.chart:
                self.chart_stack.setCurrentIndex(2)
            else:
                self.bar.set_points(result.chart)
                self.chart_stack.setCurrentIndex(0)
        self.actions.btn_more.setEnabled(self.controller.has_more())
        self.status.setText(f"{result.title} · {len(result.rows)} vrstic")

    def load_more(self) -> None:
        self.controller.more()
        result = self.controller.result
        if result and result.key != "dashboard":
            self.table.set_report(result.headers, self.controller.visible_rows())
            self.actions.btn_more.setEnabled(self.controller.has_more())

    def export_pdf(self) -> None:
        result = self.controller.result
        if result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF", str(self.controller.service.export_start("pdf")), "PDF (*.pdf)"
        )
        if not path:
            return
        self.controller.service.export_pdf(result, Path(path))
        toast(self, "PDF ustvarjen")

    def export_excel(self) -> None:
        result = self.controller.result
        if result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel", str(self.controller.service.export_start("xlsx")), "Excel (*.xlsx)"
        )
        if not path:
            return
        self.controller.service.export_excel(result, Path(path))
        toast(self, "Excel izvožen")

    def export_csv(self) -> None:
        result = self.controller.result
        if result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV", str(self.controller.service.export_start("csv")), "CSV (*.csv)"
        )
        if not path:
            return
        self.controller.service.export_csv(result, Path(path))
        toast(self, "CSV izvožen")

    def print_report(self) -> None:
        result = self.controller.result
        if result is None:
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        document = QTextDocument()
        document.setHtml(self.controller.service.print_html(result))
        document.print_(printer)
