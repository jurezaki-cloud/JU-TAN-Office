from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.brand_icons import brand_icon
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.payment_repository import payment_repository
from app.theme.colors import semantic_color
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.cards.revenue_chart import SLO_MONTHS, RevenueChart
from app.widgets.invoices.status_badge import StatusBadgeDelegate, invoice_badge

SLO_MONTHS_FULL = (
    "januar", "februar", "marec", "april", "maj", "junij",
    "julij", "avgust", "september", "oktober", "november", "december",
)


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

        self._canvas = QWidget()
        self._canvas.setObjectName("DashboardCanvas")
        self._grid = QGridLayout(self._canvas)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)

        self._welcome = self._build_welcome()
        self._kpi_invoices = KpiCard("Število računov", "0", "Vsi dokumenti")
        self._kpi_revenue = KpiCard("Promet", "0,00 €", "Skupni promet")
        self._kpi_unpaid = KpiCard("Neplačano", "0,00 €", "Odprti računi")
        self._kpi_overdue = KpiCard("Zapadlo", "0,00 €", "Po roku plačila")
        self._chart_card = self._build_chart_card()
        self._quick_card = self._build_quick_card()
        self._invoices_card = self._build_invoices_card()
        self._activity_card = self._build_activity_card()

        scroll.setWidget(self._canvas)
        outer.addWidget(scroll)

        self._breakpoint = None
        self._place_widgets(1400)
        self.refresh()

    def _build_welcome(self) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("DashboardWelcomeBlock")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(2, 0, 2, 4)
        layout.setSpacing(12)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)

        hello = QLabel("Pregled poslovanja")
        hello.setObjectName("DashboardWelcome")

        self._date_label = QLabel(self._today_label())
        self._date_label.setObjectName("DashboardDate")

        text.addWidget(hello)
        text.addWidget(self._date_label)

        layout.addLayout(text)
        layout.addStretch()
        return wrap

    def _build_chart_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Promet")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Zadnjih 6 mesecev")
        caption.setObjectName("DashboardMuted")
        self.chart = RevenueChart()
        card.body.addWidget(title)
        card.body.addWidget(caption)
        card.body.addWidget(self.chart, 1)
        return card

    def _build_quick_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Hitre akcije")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        muted = semantic_color("TEXT", "#0F172A")
        self.btn_new_invoice = QPushButton("Nov račun")
        self.btn_new_invoice.setObjectName("PrimaryButton")
        self.btn_new_invoice.setIcon(brand_icon("invoices", color="#FFFFFF", size=14))

        self.btn_new_offer = QPushButton("Nova ponudba")
        self.btn_new_offer.setObjectName("SecondaryButton")
        self.btn_new_offer.setIcon(brand_icon("offers", color=muted, size=14))

        self.btn_new_customer = QPushButton("Nova stranka")
        self.btn_new_customer.setObjectName("SecondaryButton")
        self.btn_new_customer.setIcon(brand_icon("customers", color=muted, size=14))

        self.btn_new_article = QPushButton("Nov artikel")
        self.btn_new_article.setObjectName("GhostButton")
        self.btn_new_article.setIcon(brand_icon("articles", color=muted, size=14))

        for button in (
            self.btn_new_invoice,
            self.btn_new_offer,
            self.btn_new_customer,
            self.btn_new_article,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            card.body.addWidget(button)

        card.body.addStretch()

        self.btn_new_invoice.clicked.connect(self.new_invoice_requested.emit)
        self.btn_new_offer.clicked.connect(self.new_offer_requested.emit)
        self.btn_new_customer.clicked.connect(self.new_customer_requested.emit)
        self.btn_new_article.clicked.connect(self.new_article_requested.emit)
        return card

    def _build_invoices_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Zadnji računi")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

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
        card.body.addWidget(self.invoice_table)
        return card

    def _build_activity_card(self) -> EnterpriseCard:
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Zadnje aktivnosti")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        self.activity_list = QListWidget()
        self.activity_list.setObjectName("DashboardActivity")
        self.activity_list.setMinimumHeight(200)
        self.activity_list.setFocusPolicy(Qt.NoFocus)
        card.body.addWidget(self.activity_list)
        return card

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
            self._kpi_invoices,
            self._kpi_revenue,
            self._kpi_unpaid,
            self._kpi_overdue,
        )

        if mode == "wide":
            self._grid.addWidget(self._welcome, 0, 0, 1, 4)
            for column, card in enumerate(kpis):
                self._grid.addWidget(card, 1, column)
            self._grid.addWidget(self._chart_card, 2, 0, 1, 3)
            self._grid.addWidget(self._quick_card, 2, 3)
            self._grid.addWidget(self._invoices_card, 3, 0, 1, 2)
            self._grid.addWidget(self._activity_card, 3, 2, 1, 2)
            for column in range(4):
                self._grid.setColumnStretch(column, 1)
        elif mode == "medium":
            self._grid.addWidget(self._welcome, 0, 0, 1, 2)
            self._grid.addWidget(self._kpi_invoices, 1, 0)
            self._grid.addWidget(self._kpi_revenue, 1, 1)
            self._grid.addWidget(self._kpi_unpaid, 2, 0)
            self._grid.addWidget(self._kpi_overdue, 2, 1)
            self._grid.addWidget(self._chart_card, 3, 0, 1, 2)
            self._grid.addWidget(self._quick_card, 4, 0, 1, 2)
            self._grid.addWidget(self._invoices_card, 5, 0)
            self._grid.addWidget(self._activity_card, 5, 1)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 1)
            self._grid.setColumnStretch(2, 0)
            self._grid.setColumnStretch(3, 0)
        else:
            self._grid.addWidget(self._welcome, 0, 0)
            row = 1
            for card in kpis:
                self._grid.addWidget(card, row, 0)
                row += 1
            self._grid.addWidget(self._chart_card, row, 0)
            self._grid.addWidget(self._quick_card, row + 1, 0)
            self._grid.addWidget(self._invoices_card, row + 2, 0)
            self._grid.addWidget(self._activity_card, row + 3, 0)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)
            self._grid.setColumnStretch(2, 0)
            self._grid.setColumnStretch(3, 0)

    def refresh(self):
        invoices = invoice_repository.get_all()
        offers = offer_repository.get_all()
        customers = customer_repository.get_all()
        revenue = float(invoice_repository.get_total_revenue() or 0)
        unpaid = 0.0
        overdue = 0.0
        for row in invoices:
            full = invoice_repository.get_by_id(row[0])
            due = full[4] if full else None
            badge = invoice_badge(row[5], due)
            total = float(row[4] or 0)
            outstanding = payment_repository.remaining(row[0], total)
            if badge in ("Neplačano", "Delno plačano", "Zapadlo"):
                unpaid += outstanding
            if badge == "Zapadlo":
                overdue += outstanding

        self._date_label.setText(self._today_label())
        self._kpi_invoices.set_value(str(len(invoices)))
        self._kpi_revenue.set_value(self._money(revenue))
        self._kpi_unpaid.set_value(self._money(unpaid))
        self._kpi_overdue.set_value(self._money(overdue))

        self.chart.set_points(self._chart_points())
        self._fill_invoices(invoices[:8])
        self._fill_activity(invoices, offers, customers)

    def _chart_points(self) -> list[tuple[str, float]]:
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

    def _fill_invoices(self, rows) -> None:
        self.invoice_table.setRowCount(len(rows))
        if not rows:
            self.invoice_table.setRowCount(1)
            empty = QTableWidgetItem("Ni računov")
            empty.setFlags(Qt.NoItemFlags)
            self.invoice_table.setItem(0, 0, empty)
            self.invoice_table.setSpan(0, 0, 1, 4)
            return

        self.invoice_table.clearSpans()
        for row, invoice in enumerate(rows):
            number = str(invoice[1] if len(invoice) > 1 else "")
            issued = str(invoice[2] if len(invoice) > 2 else "")
            total = invoice[4] if len(invoice) > 4 else 0
            raw_status = str(invoice[5] if len(invoice) > 5 else "")
            full = invoice_repository.get_by_id(invoice[0]) if invoice else None
            due = full[4] if full else None
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
            item = QListWidgetItem("Ni zadnjih aktivnosti")
            self.activity_list.addItem(item)
            return

        for text in events[:8]:
            self.activity_list.addItem(QListWidgetItem(text))

    @staticmethod
    def _money(value) -> str:
        from app.utils.money import format_eur

        return format_eur(value)

    @staticmethod
    def _today_label() -> str:
        today = date.today()
        weekday = (
            "ponedeljek", "torek", "sreda", "četrtek",
            "petek", "sobota", "nedelja",
        )[today.weekday()]
        month = SLO_MONTHS_FULL[today.month - 1]
        return f"{weekday.capitalize()}, {today.day}. {month} {today.year}"
