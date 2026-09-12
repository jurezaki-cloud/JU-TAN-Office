from PySide6.QtWidgets import QHBoxLayout, QWidget

from app.widgets.cards.kpi_card import KpiCard


class CrmDashboard(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CrmDashboard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.kpi_leads = KpiCard("Lead Count", "0", "Stage Lead")
        self.kpi_active = KpiCard("Active Deals", "0", "V pogajanjih")
        self.kpi_won = KpiCard("Won Deals", "0", "Dobljeno")
        self.kpi_lost = KpiCard("Lost Deals", "0", "Izgubljeno")
        self.kpi_meetings = KpiCard("Meetings Today", "0", "Sestanki")
        self.kpi_calls = KpiCard("Calls Today", "0", "Klici")
        for card in (
            self.kpi_leads,
            self.kpi_active,
            self.kpi_won,
            self.kpi_lost,
            self.kpi_meetings,
            self.kpi_calls,
        ):
            layout.addWidget(card)

    def set_kpis(self, data: dict) -> None:
        self.kpi_leads.set_value(str(data.get("leads", 0)))
        self.kpi_active.set_value(str(data.get("active", 0)))
        self.kpi_won.set_value(str(data.get("won", 0)))
        self.kpi_lost.set_value(str(data.get("lost", 0)))
        self.kpi_meetings.set_value(str(data.get("meetings", 0)))
        self.kpi_calls.set_value(str(data.get("calls", 0)))
