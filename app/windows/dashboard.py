from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.theme.tokens import SPACE_3, SPACE_4
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.cards.revenue_chart import SLO_MONTHS, RevenueChart
from app.widgets.dashboard.quick_actions import QuickActionsCard
from app.widgets.dashboard.system_health import DashboardHealthCard
from app.widgets.dashboard.welcome_header import WelcomeHeader
from app.widgets.invoices.status_badge import StatusBadgeDelegate, invoice_badge


class Dashboard(QWidget):
    new_invoice_requested = Signal()
    new_offer_requested = Signal()
    new_customer_requested = Signal()
    new_article_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("DashboardPage")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("DashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setAttribute(Qt.WA_StyledBackground, True)

        self._canvas = QWidget()
        self._canvas.setObjectName("DashboardCanvas")
        self._canvas.setAttribute(Qt.WA_StyledBackground, True)
        self._grid = QGridLayout(self._canvas)
        self._grid.setContentsMargins(SPACE_4, SPACE_3, SPACE_4, SPACE_4)
        self._grid.setHorizontalSpacing(SPACE_3)
        self._grid.setVerticalSpacing(SPACE_4)

        self._welcome = WelcomeHeader()
        # Primary business KPI first — visually dominant; values/calc unchanged.
        self._kpi_revenue = KpiCard(
            "Promet", "0,00 €", "Skupni promet", tone="primary", dominant=True
        )
        self._kpi_unpaid = KpiCard(
            "Neplačano", "0,00 €", "Odprti računi", tone="warning"
        )
        self._kpi_overdue = KpiCard(
            "Zapadlo", "0,00 €", "Po roku plačila", tone="danger"
        )
        self._kpi_invoices = KpiCard(
            "Število računov", "0", "Vsi dokumenti", tone="neutral"
        )
        self._chart_card = self._build_chart_card()
        self._quick_card = QuickActionsCard()
        self._health_card = DashboardHealthCard()
        self._invoices_card = self._build_invoices_card()
        self._activity_card = self._build_activity_card()

        self._quick_card.new_invoice_requested.connect(self.new_invoice_requested.emit)
        self._quick_card.new_offer_requested.connect(self.new_offer_requested.emit)
        self._quick_card.new_customer_requested.connect(self.new_customer_requested.emit)
        self._quick_card.new_article_requested.connect(self.new_article_requested.emit)

        # Backward-compatible aliases used by older UI helpers / polish scripts.
        self.btn_new_invoice = self._quick_card.btn_new_invoice
        self.btn_new_offer = self._quick_card.btn_new_offer
        self.btn_new_customer = self._quick_card.btn_new_customer
        self.btn_new_article = self._quick_card.btn_new_article

        scroll.setWidget(self._canvas)
        outer.addWidget(scroll)

        self._breakpoint = None
        self._data_loaded = False
        self._place_widgets(1400)
        # Defer DB-heavy refresh until first paint so MainWindow can show sooner.

    def _build_chart_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        eyebrow = QLabel("FINANČNI PREGLED")
        eyebrow.setObjectName("DashboardEyebrow")
        title = QLabel("Promet po mesecih")
        title.setObjectName("DashboardSectionTitle")
        self._chart_caption = QLabel("Zadnjih 6 mesecev")
        self._chart_caption.setObjectName("DashboardMuted")
        self.chart = RevenueChart()
        card.body.addWidget(eyebrow)
        card.body.addWidget(title)
        card.body.addWidget(self._chart_caption)
        card.body.addWidget(self.chart, 1)
        return card

    def _build_invoices_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        eyebrow = QLabel("DOKUMENTI")
        eyebrow.setObjectName("DashboardEyebrow")
        title = QLabel("Zadnji računi")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Najnovejši izdani dokumenti")
        caption.setObjectName("DashboardMuted")
        card.body.addWidget(eyebrow)
        card.body.addWidget(title)
        card.body.addWidget(caption)

        self.invoice_table = QTableWidget(0, 4)
        self.invoice_table.setObjectName("DashboardTable")
        self.invoice_table.setHorizontalHeaderLabels(
            ["Številka", "Datum", "Znesek", "Status"]
        )
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.verticalHeader().setDefaultSectionSize(40)
        self.invoice_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setSelectionMode(QTableWidget.SingleSelection)
        self.invoice_table.setShowGrid(False)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.setFocusPolicy(Qt.NoFocus)
        self.invoice_table.horizontalHeader().setStretchLastSection(True)
        self.invoice_table.setMinimumHeight(200)
        self.invoice_table.setItemDelegateForColumn(3, StatusBadgeDelegate(self.invoice_table))

        self._invoices_empty = QLabel(
            "Ni računov\nUstvarite prvi račun za pregled dokumentov."
        )
        self._invoices_empty.setObjectName("DashboardEmptyState")
        self._invoices_empty.setAlignment(Qt.AlignCenter)
        self._invoices_empty.setWordWrap(True)
        self._invoices_empty.setMinimumHeight(200)

        self._invoices_stack = QStackedWidget()
        self._invoices_stack.addWidget(self.invoice_table)
        self._invoices_stack.addWidget(self._invoices_empty)
        card.body.addWidget(self._invoices_stack)
        return card

    def _build_activity_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        eyebrow = QLabel("AKTIVNOST")
        eyebrow.setObjectName("DashboardEyebrow")
        title = QLabel("Zadnje aktivnosti")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Računi, ponudbe in stranke")
        caption.setObjectName("DashboardMuted")
        card.body.addWidget(eyebrow)
        card.body.addWidget(title)
        card.body.addWidget(caption)

        self.activity_list = QListWidget()
        self.activity_list.setObjectName("DashboardActivity")
        self.activity_list.setMinimumHeight(200)
        self.activity_list.setFocusPolicy(Qt.NoFocus)

        self._activity_empty = QLabel(
            "Ni zadnjih aktivnosti\nRačuni, ponudbe in stranke se prikažejo tukaj."
        )
        self._activity_empty.setObjectName("DashboardEmptyState")
        self._activity_empty.setAlignment(Qt.AlignCenter)
        self._activity_empty.setWordWrap(True)
        self._activity_empty.setMinimumHeight(200)

        self._activity_stack = QStackedWidget()
        self._activity_stack.addWidget(self.activity_list)
        self._activity_stack.addWidget(self._activity_empty)
        card.body.addWidget(self._activity_stack)
        return card

    def showEvent(self, event):
        super().showEvent(event)
        if not self._data_loaded:
            from app.core.async_load import defer

            defer(self.refresh)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_widgets(self.width())

    def _place_widgets(self, width: int) -> None:
        # Breakpoints measured on the dashboard page (inside the shell chrome).
        if width >= 1100:
            mode = "wide"
        elif width >= 760:
            mode = "medium"
        else:
            mode = "narrow"

        if mode == self._breakpoint:
            return

        self._breakpoint = mode
        self._canvas.setUpdatesEnabled(False)
        try:
            while self._grid.count():
                item = self._grid.takeAt(0)
                if item.widget():
                    item.widget().setParent(self._canvas)

            kpis = (
                self._kpi_revenue,
                self._kpi_unpaid,
                self._kpi_overdue,
                self._kpi_invoices,
            )

            if mode == "wide":
                self._grid.addWidget(self._welcome, 0, 0, 1, 5)
                # Hero Promet spans two columns; supporting KPIs share the rest.
                self._grid.addWidget(self._kpi_revenue, 1, 0, 1, 2)
                self._grid.addWidget(self._kpi_unpaid, 1, 2)
                self._grid.addWidget(self._kpi_overdue, 1, 3)
                self._grid.addWidget(self._kpi_invoices, 1, 4)
                self._grid.addWidget(self._chart_card, 2, 0, 1, 3)
                self._grid.addWidget(self._quick_card, 2, 3)
                self._grid.addWidget(self._health_card, 2, 4)
                self._grid.addWidget(self._invoices_card, 3, 0, 1, 3)
                self._grid.addWidget(self._activity_card, 3, 3, 1, 2)
                self._grid.setColumnStretch(0, 2)
                self._grid.setColumnStretch(1, 2)
                self._grid.setColumnStretch(2, 1)
                self._grid.setColumnStretch(3, 1)
                self._grid.setColumnStretch(4, 1)
                self._grid.setRowStretch(2, 1)
                self._grid.setRowStretch(3, 1)
            elif mode == "medium":
                self._grid.addWidget(self._welcome, 0, 0, 1, 2)
                self._grid.addWidget(self._kpi_revenue, 1, 0, 1, 2)
                self._grid.addWidget(self._kpi_unpaid, 2, 0)
                self._grid.addWidget(self._kpi_overdue, 2, 1)
                self._grid.addWidget(self._kpi_invoices, 3, 0, 1, 2)
                self._grid.addWidget(self._chart_card, 4, 0, 1, 2)
                self._grid.addWidget(self._quick_card, 5, 0)
                self._grid.addWidget(self._health_card, 5, 1)
                self._grid.addWidget(self._invoices_card, 6, 0)
                self._grid.addWidget(self._activity_card, 6, 1)
                self._grid.setColumnStretch(0, 1)
                self._grid.setColumnStretch(1, 1)
                self._grid.setColumnStretch(2, 0)
                self._grid.setColumnStretch(3, 0)
                self._grid.setColumnStretch(4, 0)
            else:
                self._grid.addWidget(self._welcome, 0, 0)
                row = 1
                for card in kpis:
                    self._grid.addWidget(card, row, 0)
                    row += 1
                self._grid.addWidget(self._chart_card, row, 0)
                self._grid.addWidget(self._quick_card, row + 1, 0)
                self._grid.addWidget(self._health_card, row + 2, 0)
                self._grid.addWidget(self._invoices_card, row + 3, 0)
                self._grid.addWidget(self._activity_card, row + 4, 0)
                self._grid.setColumnStretch(0, 1)
                self._grid.setColumnStretch(1, 0)
                self._grid.setColumnStretch(2, 0)
                self._grid.setColumnStretch(3, 0)
                self._grid.setColumnStretch(4, 0)
        finally:
            self._canvas.setUpdatesEnabled(True)

    def refresh(self):
        from app.database.customer_repository import customer_repository
        from app.database.invoice_repository import invoice_repository
        from app.database.offer_repository import offer_repository
        from app.database.payment_repository import payment_repository

        self._data_loaded = True
        self.setUpdatesEnabled(False)
        try:
            invoices = invoice_repository.get_all()
            offers = offer_repository.get_all()
            customers = customer_repository.get_all()
            revenue = float(invoice_repository.get_total_revenue() or 0)

            invoice_ids = [row[0] for row in invoices]
            due_dates = invoice_repository.get_due_dates_map(invoice_ids)
            totals_by_id = {row[0]: float(row[4] or 0) for row in invoices}
            remainings = payment_repository.remaining_map(totals_by_id)

            unpaid = 0.0
            overdue = 0.0
            for row in invoices:
                due = due_dates.get(row[0])
                badge = invoice_badge(row[5], due)
                outstanding = remainings.get(row[0], float(row[4] or 0))
                if badge in ("Neplačano", "Delno plačano", "Zapadlo"):
                    unpaid += outstanding
                if badge == "Zapadlo":
                    overdue += outstanding

            self._welcome.refresh()
            self._quick_card.refresh_icons()
            self._health_card.refresh()

            self._kpi_invoices.set_value(str(len(invoices)))
            self._kpi_revenue.set_value(self._money(revenue))
            self._kpi_unpaid.set_value(self._money(unpaid))
            self._kpi_overdue.set_value(self._money(overdue))

            self.chart.set_points(self._chart_points())
            self._fill_invoices(invoices[:8], due_dates)
            self._fill_activity(invoices, offers, customers)
        finally:
            self.setUpdatesEnabled(True)

    def _chart_points(self) -> list[tuple[str, float]]:
        from app.database.invoice_repository import invoice_repository

        monthly = {
            str(month): float(total or 0)
            for month, total in invoice_repository.get_monthly_revenue()
        }
        today = date.today()
        points = []
        for offset in range(5, -1, -1):
            month_index = today.month - offset
            year = today.year
            while month_index <= 0:
                month_index += 12
                year -= 1
            key = f"{year:04d}-{month_index:02d}"
            points.append((SLO_MONTHS[month_index - 1], monthly.get(key, 0.0)))

        return points

    def _fill_invoices(self, rows, due_dates=None) -> None:
        if not rows:
            self.invoice_table.setRowCount(0)
            self.invoice_table.clearSpans()
            self._invoices_stack.setCurrentWidget(self._invoices_empty)
            return

        self._invoices_stack.setCurrentWidget(self.invoice_table)
        self.invoice_table.clearSpans()
        self.invoice_table.setRowCount(len(rows))
        due_dates = due_dates or {}
        for row, invoice in enumerate(rows):
            number = str(invoice[1] if len(invoice) > 1 else "")
            issued = str(invoice[2] if len(invoice) > 2 else "")
            total = invoice[4] if len(invoice) > 4 else 0
            raw_status = str(invoice[5] if len(invoice) > 5 else "")
            due = due_dates.get(invoice[0]) if invoice else None
            status = invoice_badge(raw_status, due)

            values = [number, issued, self._money(total), status]
            aligns = [Qt.AlignLeft | Qt.AlignVCenter, Qt.AlignLeft | Qt.AlignVCenter,
                      Qt.AlignRight | Qt.AlignVCenter, Qt.AlignCenter]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setTextAlignment(aligns[column])
                self.invoice_table.setItem(row, column, item)

    def _fill_activity(self, invoices, offers, customers) -> None:
        self.activity_list.clear()
        events = []

        for invoice in invoices[:5]:
            number = invoice[1] if len(invoice) > 1 else ""
            issued = invoice[2] if len(invoice) > 2 else ""
            events.append(f"Račun {number}  ·  {issued}")

        for offer in offers[:4]:
            number = offer[1] if len(offer) > 1 else ""
            issued = offer[3] if len(offer) > 3 else ""
            events.append(f"Ponudba {number}  ·  {issued}")

        for customer in customers[:3]:
            name = customer[1] if len(customer) > 1 else "Stranka"
            events.append(f"Stranka {name}")

        if not events:
            self._activity_stack.setCurrentWidget(self._activity_empty)
            return

        self._activity_stack.setCurrentWidget(self.activity_list)
        for text in events[:8]:
            self.activity_list.addItem(QListWidgetItem(text))

    @staticmethod
    def _money(value) -> str:
        from app.utils.money import format_eur

        return format_eur(value)
