from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.modules.analytics.analytics_controller import AnalyticsController
from app.modules.analytics.analytics_widgets import (
    BarChart,
    ExportBar,
    LineChart,
    PeriodFilterBar,
    PieChart,
    RankingTable,
)
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard


class AnalyticsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("AnalyticsPage")
        self.controller = AnalyticsController()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("AnalyticsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._canvas = QWidget()
        self._canvas.setObjectName("AnalyticsCanvas")
        self._grid = QGridLayout(self._canvas)
        self._grid.setContentsMargins(20, 20, 20, 20)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)

        self._toolbar = self._build_toolbar()
        self._kpi_today = KpiCard("Današnji promet", "0,00 €", "Računi z današnjim datumom")
        self._kpi_month = KpiCard("Mesečni promet", "0,00 €", "Tekoči koledarski mesec")
        self._kpi_invoices = KpiCard("Izdani računi", "0", "V izbranem obdobju")
        self._kpi_customers = KpiCard("Aktivne stranke", "0", "Stranke z računi v obdobju")
        self._line_card, self.line_chart = self._build_chart_card(
            "Mesečni promet", "Linijski trend", LineChart()
        )
        self._bar_card, self.bar_chart = self._build_chart_card(
            "Prodaja po mesecih", "Stolpčni pregled", BarChart()
        )
        self._pie_card, self.pie_chart = self._build_chart_card(
            "Statusi računov", "Delež po statusu", PieChart()
        )
        self._customers_card, self.customers_table = self._build_list_card(
            "Top 10 kupcev po prometu",
            RankingTable(("Kupec", "Promet")),
        )
        self._articles_card, self.articles_table = self._build_list_card(
            "Top 10 artiklov po prodaji",
            RankingTable(("Artikel", "Količina")),
        )

        scroll.setWidget(self._canvas)
        outer.addWidget(scroll)

        self.filters.period_changed.connect(lambda _: self.refresh())
        self.filters.custom_range_changed.connect(self.refresh)
        self.exports.pdf_clicked.connect(self._export_stub)
        self.exports.excel_clicked.connect(self._export_stub)
        self.exports.print_clicked.connect(self._export_stub)

        today = date.today()
        self.filters.from_date.setDate(QDate(today.year, today.month, 1))
        self.filters.to_date.setDate(QDate(today.year, today.month, today.day))

        self._breakpoint = None
        self._place_widgets(1400)
        self.refresh()
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.analytics", tables=[self.customers_table, self.articles_table])

    def _build_toolbar(self) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("AnalyticsToolbarRow")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(4, 0, 4, 4)
        layout.setSpacing(16)

        self.filters = PeriodFilterBar()
        self.exports = ExportBar()
        layout.addWidget(self.filters, 1)
        layout.addWidget(self.exports, 0)
        return wrap

    def _build_chart_card(self, title: str, caption: str, chart):
        card = EnterpriseCard("DashboardCard")
        heading = QLabel(title)
        heading.setObjectName("DashboardSectionTitle")
        hint = QLabel(caption)
        hint.setObjectName("DashboardMuted")
        card.body.addWidget(heading)
        card.body.addWidget(hint)
        card.body.addWidget(chart, 1)
        return card, chart

    def _build_list_card(self, title: str, table: RankingTable):
        card = EnterpriseCard("DashboardCard")
        heading = QLabel(title)
        heading.setObjectName("DashboardSectionTitle")
        hint = QLabel("Po izbranem obdobju")
        hint.setObjectName("DashboardMuted")
        card.body.addWidget(heading)
        card.body.addWidget(hint)
        card.body.addWidget(table, 1)
        return card, table

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_widgets(self.width())

    def _place_widgets(self, width: int) -> None:
        if width >= 1100:
            mode = "wide"
        elif width >= 760:
            mode = "medium"
        else:
            mode = "narrow"

        if mode == self._breakpoint:
            return
        self._breakpoint = mode

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(self._canvas)

        kpis = (
            self._kpi_today,
            self._kpi_month,
            self._kpi_invoices,
            self._kpi_customers,
        )

        if mode == "wide":
            self._grid.addWidget(self._toolbar, 0, 0, 1, 4)
            for column, card in enumerate(kpis):
                self._grid.addWidget(card, 1, column)
            self._grid.addWidget(self._line_card, 2, 0, 1, 2)
            self._grid.addWidget(self._pie_card, 2, 2, 1, 2)
            self._grid.addWidget(self._bar_card, 3, 0, 1, 4)
            self._grid.addWidget(self._customers_card, 4, 0, 1, 2)
            self._grid.addWidget(self._articles_card, 4, 2, 1, 2)
            for column in range(4):
                self._grid.setColumnStretch(column, 1)
        elif mode == "medium":
            self._grid.addWidget(self._toolbar, 0, 0, 1, 2)
            self._grid.addWidget(self._kpi_today, 1, 0)
            self._grid.addWidget(self._kpi_month, 1, 1)
            self._grid.addWidget(self._kpi_invoices, 2, 0)
            self._grid.addWidget(self._kpi_customers, 2, 1)
            self._grid.addWidget(self._line_card, 3, 0, 1, 2)
            self._grid.addWidget(self._bar_card, 4, 0, 1, 2)
            self._grid.addWidget(self._pie_card, 5, 0, 1, 2)
            self._grid.addWidget(self._customers_card, 6, 0)
            self._grid.addWidget(self._articles_card, 6, 1)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 1)
            self._grid.setColumnStretch(2, 0)
            self._grid.setColumnStretch(3, 0)
        else:
            self._grid.addWidget(self._toolbar, 0, 0)
            row = 1
            for card in kpis:
                self._grid.addWidget(card, row, 0)
                row += 1
            for card in (
                self._line_card,
                self._bar_card,
                self._pie_card,
                self._customers_card,
                self._articles_card,
            ):
                self._grid.addWidget(card, row, 0)
                row += 1
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)
            self._grid.setColumnStretch(2, 0)
            self._grid.setColumnStretch(3, 0)

    def refresh(self):
        period = self.filters.current_period()
        q_from = self.filters.from_date.date()
        q_to = self.filters.to_date.date()
        snapshot = self.controller.snapshot(
            period=period,
            custom_from=date(q_from.year(), q_from.month(), q_from.day()),
            custom_to=date(q_to.year(), q_to.month(), q_to.day()),
        )

        self._kpi_today.set_value(self._money(snapshot.today_revenue))
        self._kpi_month.set_value(self._money(snapshot.month_revenue))
        self._kpi_invoices.set_value(str(snapshot.invoice_count))
        self._kpi_customers.set_value(str(snapshot.active_customers))

        self.line_chart.set_points(snapshot.line_points)
        self.bar_chart.set_points(snapshot.bar_points)
        self.pie_chart.set_slices(snapshot.status_slices)

        self._set_caption(
            self._line_card,
            "Vzorčni trend" if snapshot.mock_charts else "Linijski trend",
        )
        self._set_caption(
            self._bar_card,
            "Vzorčni prikaz" if snapshot.mock_charts else "Stolpčni pregled",
        )
        self._set_caption(
            self._pie_card,
            "Vzorčni statusi" if snapshot.mock_status else "Delež po statusu",
        )
        self._set_caption(
            self._customers_card,
            "Vzorčni seznam" if snapshot.mock_customers else "Po izbranem obdobju",
        )
        self._set_caption(
            self._articles_card,
            "Vzorčni seznam" if snapshot.mock_articles else "Po izbranem obdobju",
        )

        self.customers_table.set_rows([
            (name, self._money(value)) for name, value in snapshot.top_customers
        ])
        self.articles_table.set_rows([
            (name, self._qty(value)) for name, value in snapshot.top_articles
        ])

    def _export_stub(self):
        QMessageBox.information(
            self,
            "Analytics",
            self.controller.export_notice(),
        )

    @staticmethod
    def _set_caption(card: EnterpriseCard, text: str) -> None:
        for index in range(card.body.count()):
            widget = card.body.itemAt(index).widget()
            if isinstance(widget, QLabel) and widget.objectName() == "DashboardMuted":
                widget.setText(text)
                return

    @staticmethod
    def _money(value) -> str:
        try:
            return f"{float(value):,.2f} €".replace(",", " ")
        except (TypeError, ValueError):
            return "0.00 €"

    @staticmethod
    def _qty(value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "0"
        if number.is_integer():
            return str(int(number))
        return f"{number:.2f}"
