from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from app.services.analytics_service import analytics_service
from app.widgets.messages import show_error


class StatCard(QFrame):
    def __init__(self, title, value="—", accent="#0F766E"):
        super().__init__()
        self.setStyleSheet(
            "QFrame{background:white;border:1px solid #dbe4e6;"
            "border-radius:12px;}"
        )
        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:13px;color:#64748b;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size:25px;font-weight:bold;color:{accent};"
        )
        layout.addWidget(title_label); layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(value)


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size:28px;font-weight:bold;")
        layout.addWidget(title)
        grid = QGridLayout()
        self.revenue = StatCard("Prejeta plačila letos")
        self.open_amount = StatCard("Odprte terjatve", accent="#D97706")
        self.overdue = StatCard("Zapadle terjatve", accent="#DC2626")
        self.invoices = StatCard("Računi")
        self.customers = StatCard("Stranke")
        self.offers = StatCard("Ponudbe")
        for position, card in enumerate((
            self.revenue, self.open_amount, self.overdue,
            self.invoices, self.customers, self.offers,
        )):
            grid.addWidget(card, position // 3, position % 3)
        layout.addLayout(grid)
        self.message = QLabel(
            "Podrobne mesečne rezultate, terjatve in najboljše stranke najdete "
            "v zavihku Analitika."
        )
        self.message.setStyleSheet(
            "background:#f0fdfa;color:#115e59;padding:18px;border-radius:10px;"
        )
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        try:
            data = analytics_service.summary()
            self.revenue.set_value(f'{data["revenue"]:,.2f} €')
            self.open_amount.set_value(f'{data["open_amount"]:,.2f} €')
            self.overdue.set_value(
                f'{data["overdue_amount"]:,.2f} € ({data["overdue_count"]})'
            )
            self.invoices.set_value(str(data["invoices"]))
            self.customers.set_value(str(data["customers"]))
            self.offers.set_value(str(data["offers"]))
        except Exception as error:
            show_error(self, error, "Dashboarda ni mogoče osvežiti")
