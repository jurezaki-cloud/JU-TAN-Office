from PySide6.QtWidgets import QLabel

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.customers.customer_form import CustomerForm


class CustomerDialog(EnterpriseDialog):

    def __init__(self, parent=None, customer=None):
        title = "Uredi stranko" if customer else "Nova stranka"
        super().__init__(parent, title=title, heading=title, size="SMALL", state_key="dialog.customer")
        self.customer = customer
        self.setObjectName("CustomerDialog")

        card = EnterpriseCard("DashboardCard")
        self.form = CustomerForm()
        card.body.addWidget(self.form)
        self.body.addWidget(card)
        self.form.load(customer)

    def get_data(self):
        return self.form.get_data()
