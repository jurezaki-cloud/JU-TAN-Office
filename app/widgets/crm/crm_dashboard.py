from PySide6.QtWidgets import QGridLayout, QWidget

from app.widgets.cards.kpi_card import KpiCard
from app.utils.money import format_eur


class CrmDashboard(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CrmDashboard")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        self.new_customers = KpiCard("Nove stranke", "0", "Ta mesec")
        self.active_customers = KpiCard("Aktivne stranke", "0", "Stranke s poslovanjem")
        self.open_offers = KpiCard("Odprte ponudbe", "0", "0,00 €")
        self.to_contact = KpiCard("Za kontaktirati", "0", "Danes in zapadlo")
        self.opportunities = KpiCard("Prodajne priložnosti", "0", "Aktivni posli")
        self.pipeline_value = KpiCard("Vrednost priložnosti", "0,00 €", "Odprt pipeline")

        cards = (
            self.new_customers, self.active_customers, self.open_offers,
            self.to_contact, self.opportunities, self.pipeline_value,
        )
        for index, card in enumerate(cards):
            layout.addWidget(card, index // 3, index % 3)

    def set_kpis(self, data: dict) -> None:
        self.new_customers.set_value(str(data.get("new_customers", 0)))
        self.active_customers.set_value(str(data.get("active_customers", 0)))
        self.open_offers.set_value(str(data.get("open_offers", 0)))
        self.open_offers.hint.setText(format_eur(data.get("open_offers_value", 0)))
        self.to_contact.set_value(str(data.get("to_contact", 0)))
        self.opportunities.set_value(str(data.get("opportunities", 0)))
        self.pipeline_value.set_value(format_eur(data.get("pipeline_value", 0)))


