from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QTabWidget

from app.utils.money import format_eur
from app.widgets.cards.enterprise_card import EnterpriseCard


class CustomerCard(EnterpriseCard):
    customer_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__("DashboardCard", parent)
        self.setObjectName("CustomerCard")

        title = QLabel("Stranka 360°")
        title.setObjectName("SectionTitle")
        self.body.addWidget(title)

        self.list = QListWidget()
        self.list.setObjectName("EnterpriseTable")
        self.list.setMaximumHeight(120)
        self.body.addWidget(self.list)

        self.summary = QLabel("Izberi stranko za celoten CRM pregled.")
        self.summary.setObjectName("DetailValue")
        self.summary.setWordWrap(True)
        self.body.addWidget(self.summary)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("Customer360Tabs")
        self.overview = self._list_tab("Pregled")
        self.timeline = self._list_tab("Časovnica")
        self.documents = self._list_tab("Dokumenti")
        self.payments = self._list_tab("Plačila")
        self.opportunities = self._list_tab("Priložnosti")
        self.contacts = self._list_tab("Kontakti")
        self.tasks = self._list_tab("Opravila")
        self.notes = self._list_tab("Opombe")
        self.body.addWidget(self.tabs, 1)
        self.list.itemClicked.connect(self._pick)

    def _list_tab(self, caption: str) -> QListWidget:
        widget = QListWidget()
        widget.setObjectName("EnterpriseTable")
        widget.setAlternatingRowColors(True)
        self.tabs.addTab(widget, caption)
        return widget

    def set_customers(self, rows: list) -> None:
        self.list.clear()
        for row in rows:
            if row[0] is None:
                continue
            contact = str(row[2] or "").strip()
            label = str(row[1] or "Stranka")
            if contact:
                label += f"  ·  {contact}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, int(row[0]))
            self.list.addItem(item)
    def show_360(self, data: dict) -> None:
        customer = data.get("customer")
        if not customer:
            self.summary.setText("Stranka ni v registru.")
            self._clear_detail_tabs()
            return

        self.summary.setText(
            f"{customer[1]}\n"
            f"{customer[3] or ''}, {customer[4] or ''} {customer[5] or ''}\n"
            f"Kontakt: {customer[2] or '—'}  ·  {customer[9] or '—'}  ·  {customer[8] or '—'}\n"
            f"Davčna: {customer[7] or '—'}"
        )
        self._fill_overview(data)
        self._fill_timeline(data.get("timeline") or [])
        self._fill_documents(data)
        self._fill_opportunities(data)
        self._fill_payments(data.get("payments") or [])
        self._fill_contacts(data.get("contacts") or [])
        self._fill_tasks(data.get("activities") or [])
        self._fill_notes(data.get("notes") or [])

    def _fill_overview(self, data: dict) -> None:
        self.overview.clear()
        values = (
            ("Promet", format_eur(data.get("revenue", 0))),
            ("Odprti računi", format_eur(data.get("open_invoices", 0))),
            ("Računi", str(len(data.get("invoices") or []))),
            ("Ponudbe", str(len(data.get("offers") or []))),
            ("Naročila", str(len(data.get("orders") or []))),
            ("Aktivne priložnosti", str(len(data.get("opportunities") or []))),
            ("Poslani opomini", str(len(data.get("reminders") or []))),
        )
        for label, value in values:
            self.overview.addItem(f"{label}:  {value}")

    def _fill_timeline(self, rows: list) -> None:
        self.timeline.clear()
        for event in rows:
            self.timeline.addItem(
                f"{event.get('date') or '—'}  ·  {event.get('kind') or 'Dogodek'}  ·  {event.get('text') or ''}"
            )
        self._empty(self.timeline, "Ni dogodkov na časovnici.")

    def _fill_documents(self, data: dict) -> None:
        self.documents.clear()
        for kind, rows in (
            ("Račun", data.get("invoices") or []),
            ("Ponudba", data.get("offers") or []),
            ("Naročilo", data.get("orders") or []),
        ):
            for row in rows:
                number = row[1] if len(row) > 1 else "—"
                self.documents.addItem(f"{kind}  ·  {number}")
        self._empty(self.documents, "Stranka še nima poslovnih dokumentov.")

    def _fill_opportunities(self, data: dict) -> None:
        self.opportunities.clear()
        labels = {
            "Lead": "Novo", "Qualified": "Kontaktirano", "Proposal": "Ponudba",
            "Negotiation": "Pogajanja", "Won": "Dogovorjeno", "Lost": "Izgubljeno",
        }
        doc_labels = {"offer": "Ponudba", "order": "Naročilo", "invoice": "Račun"}
        linked = data.get("opportunity_documents") or {}
        for deal in data.get("all_opportunities") or []:
            docs = linked.get(int(deal[0]), [])
            path = " → ".join(
                f"{doc_labels.get(str(row[2]), str(row[2]))} {row[4] or row[3]}"
                for row in reversed(docs)
            )
            text = (
                f"{deal[3] or 'Priložnost'}  ·  "
                f"{labels.get(str(deal[5]), deal[5])}  ·  "
                f"{format_eur(deal[8] or 0)}  ·  {deal[6] or 'Brez skrbnika'}"
            )
            if path:
                text += f"\n{path}"
            self.opportunities.addItem(text)
        self._empty(self.opportunities, "Stranka še nima CRM priložnosti.")

    def _fill_payments(self, rows: list) -> None:
        self.payments.clear()
        for row in rows:
            number = row[1] if len(row) > 1 else "—"
            total = row[4] if len(row) > 4 else 0
            self.payments.addItem(f"{number}  ·  {format_eur(total)}")
        self._empty(self.payments, "Ni evidentiranih plačanih računov.")

    def _fill_contacts(self, rows: list) -> None:
        self.contacts.clear()
        for row in rows:
            name = row[3] if len(row) > 3 else ""
            email = row[4] if len(row) > 4 else ""
            phone = row[5] if len(row) > 5 else ""
            self.contacts.addItem(f"{name or 'Kontakt'}  ·  {phone or '—'}  ·  {email or '—'}")
        self._empty(self.contacts, "Ni dodatnih CRM kontaktov.")

    def _fill_tasks(self, rows: list) -> None:
        self.tasks.clear()
        for row in rows:
            if len(row) > 9 and row[9]:
                continue
            kind = row[4] if len(row) > 4 else "Opravilo"
            title = row[5] if len(row) > 5 else ""
            due = str(row[6] or "")[:10] if len(row) > 6 else ""
            self.tasks.addItem(f"{kind}  ·  {title or '—'}  ·  {due or 'brez roka'}")
        self._empty(self.tasks, "Ni odprtih opravil.")

    def _fill_notes(self, rows: list) -> None:
        self.notes.clear()
        for row in rows:
            body = row[3] if len(row) > 3 else ""
            owner = row[4] if len(row) > 4 else ""
            self.notes.addItem(f"{owner or 'Opomba'}  ·  {body or '—'}")
        self._empty(self.notes, "Ni CRM opomb.")

    @staticmethod
    def _empty(widget: QListWidget, text: str) -> None:
        if widget.count() == 0:
            item = QListWidgetItem(text)
            item.setFlags(Qt.NoItemFlags)
            widget.addItem(item)

    def _clear_detail_tabs(self) -> None:
        for widget in (
            self.overview, self.timeline, self.documents, self.opportunities,
            self.payments, self.contacts, self.tasks, self.notes,
        ):
            widget.clear()

    def _pick(self, item: QListWidgetItem) -> None:
        self.customer_selected.emit(int(item.data(Qt.UserRole)))
