from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from app.widgets.cards.enterprise_card import EnterpriseCard


class CustomerCard(EnterpriseCard):
    customer_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__("DashboardCard", parent)
        self.setObjectName("CustomerCard")

        title = QLabel("Customer 360")
        title.setObjectName("SectionTitle")
        self.body.addWidget(title)

        self.list = QListWidget()
        self.list.setObjectName("EnterpriseTable")
        self.list.setMaximumHeight(140)
        self.body.addWidget(self.list)

        self.summary = QLabel("Izberi stranko")
        self.summary.setObjectName("KpiHint")
        self.summary.setWordWrap(True)
        self.body.addWidget(self.summary)

        self.timeline = QLabel("")
        self.timeline.setObjectName("DetailValue")
        self.timeline.setWordWrap(True)
        self.timeline.setAlignment(Qt.AlignTop)
        self.body.addWidget(self.timeline, 1)

        self.list.itemClicked.connect(self._pick)

    def set_customers(self, rows: list) -> None:
        self.list.clear()
        for row in rows:
            if row[0] is None:
                continue
            item = QListWidgetItem(f"{row[1]} · {row[2] or ''}")
            item.setData(Qt.UserRole, int(row[0]))
            self.list.addItem(item)

    def show_360(self, data: dict) -> None:
        customer = data.get("customer")
        if not customer:
            self.summary.setText("Stranka ni v registru.")
            self.timeline.setText("")
            return
        self.summary.setText(
            f"{customer[1]}\n"
            f"Kontakt: {customer[2] or '—'} · {customer[9] or '—'} · {customer[8] or '—'}\n"
            f"Davčna: {customer[7] or '—'}\n"
            f"Promet: {_money(data.get('revenue'))} · Odprti računi: {_money(data.get('open_invoices'))}\n"
            f"Računi: {len(data.get('invoices') or [])} · "
            f"Ponudbe: {len(data.get('offers') or [])} · "
            f"Naročila: {len(data.get('orders') or [])} · "
            f"Plačila: {len(data.get('payments') or [])} · "
            f"Dokumenti: {len(data.get('documents') or [])} · "
            f"Aktivnosti: {len(data.get('activities') or [])}"
        )
        lines = []
        for event in data.get("timeline") or []:
            lines.append(f"{event.get('date') or '—'} · {event.get('kind')} · {event.get('text')}")
        self.timeline.setText("\n".join(lines) or "Ni dogodkov na časovnici.")

    def _pick(self, item: QListWidgetItem) -> None:
        self.customer_selected.emit(int(item.data(Qt.UserRole)))


def _money(value) -> str:
    try:
        return f"{float(value or 0):,.2f} €".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 €"
