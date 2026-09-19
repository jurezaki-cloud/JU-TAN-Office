from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.services.analytics_service import analytics_service
from app.widgets.messages import show_error


class StatCard(QFrame):
    def __init__(self, title, value="—", accent="#19D3C5", hint=""):
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(132)
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
            }}
            QLabel#CardTitle {{
                color: #64748B;
                font-size: 9pt;
                font-weight: 600;
            }}
            QLabel#CardValue {{
                color: {accent};
                font-size: 24px;
                font-weight: 750;
            }}
            QLabel#CardHint {{
                color: #94A3B8;
                font-size: 8pt;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 15)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("CardValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("CardHint")
            layout.addWidget(hint_label)

    def set_value(self, value):
        self.value_label.setText(value)


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(18)

        intro = QHBoxLayout()
        intro.setSpacing(12)

        copy = QVBoxLayout()
        copy.setSpacing(3)
        eyebrow = QLabel("DANES V JU-TAN OFFICE")
        eyebrow.setStyleSheet(
            "color:#0F766E;font-size:8pt;font-weight:800;letter-spacing:1px;"
        )
        title = QLabel("Vaše poslovanje na enem mestu")
        title.setProperty("role", "pageTitle")
        subtitle = QLabel(
            "Hiter pregled denarnega toka, odprtih obveznosti in poslovne aktivnosti."
        )
        subtitle.setProperty("role", "pageSubtitle")
        copy.addWidget(eyebrow)
        copy.addWidget(title)
        copy.addWidget(subtitle)
        intro.addLayout(copy)
        intro.addStretch()
        root.addLayout(intro)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.revenue = StatCard(
            "Prejeta plačila letos", accent="#0F766E", hint="Realizirani prilivi"
        )
        self.open_amount = StatCard(
            "Odprte terjatve", accent="#D97706", hint="Še neplačani računi"
        )
        self.overdue = StatCard(
            "Zapadle terjatve", accent="#DC2626", hint="Potrebna pozornost"
        )
        self.invoices = StatCard(
            "Računi", accent="#2563EB", hint="Skupno število računov"
        )
        self.customers = StatCard(
            "Stranke", accent="#7C3AED", hint="Aktivne poslovne stranke"
        )
        self.offers = StatCard(
            "Ponudbe", accent="#0891B2", hint="Skupno število ponudb"
        )

        cards = (
            self.revenue, self.open_amount, self.overdue,
            self.invoices, self.customers, self.offers,
        )
        for position, card in enumerate(cards):
            grid.addWidget(card, position // 3, position % 3)
            grid.setColumnStretch(position % 3, 1)

        root.addLayout(grid)

        insight = QFrame()
        insight.setObjectName("InsightPanel")
        insight.setStyleSheet("""
            QFrame#InsightPanel {
                background: #0F1B2D;
                border: 1px solid #172A45;
                border-radius: 14px;
            }
            QLabel#InsightEyebrow {
                color: #5EEADF;
                font-size: 8pt;
                font-weight: 800;
            }
            QLabel#InsightTitle {
                color: #FFFFFF;
                font-size: 14pt;
                font-weight: 700;
            }
            QLabel#InsightText {
                color: #AFC0D3;
                font-size: 9pt;
            }
        """)
        insight_layout = QVBoxLayout(insight)
        insight_layout.setContentsMargins(22, 18, 22, 18)
        insight_layout.setSpacing(5)

        insight_eyebrow = QLabel("POSLOVNI PREGLED")
        insight_eyebrow.setObjectName("InsightEyebrow")
        insight_title = QLabel("Podrobnejši rezultati so v Analitiki")
        insight_title.setObjectName("InsightTitle")
        self.message = QLabel(
            "Tam najdete mesečne rezultate, odprte in zapadle terjatve "
            "ter pregled najpomembnejših strank."
        )
        self.message.setObjectName("InsightText")
        self.message.setWordWrap(True)

        insight_layout.addWidget(insight_eyebrow)
        insight_layout.addWidget(insight_title)
        insight_layout.addWidget(self.message)
        root.addWidget(insight)
        root.addStretch()

        self.refresh()

    def refresh(self):
        try:
            data = analytics_service.summary()
            self.revenue.set_value(f'{data["revenue"]:,.2f} €')
            self.open_amount.set_value(f'{data["open_amount"]:,.2f} €')
            self.overdue.set_value(
                f'{data["overdue_amount"]:,.2f} €  ·  {data["overdue_count"]}'
            )
            self.invoices.set_value(str(data["invoices"]))
            self.customers.set_value(str(data["customers"]))
            self.offers.set_value(str(data["offers"]))
        except Exception as error:
            show_error(self, error, "Dashboarda ni mogoče osvežiti")
