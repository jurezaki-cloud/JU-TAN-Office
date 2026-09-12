from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFileDialog,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.modules.crm.crm_controller import CrmController
from app.widgets.crm.activity_panel import ActivityPanel
from app.widgets.crm.crm_dashboard import CrmDashboard
from app.widgets.crm.crm_dialogs import ActivityDialog, LeadDialog
from app.widgets.crm.crm_toolbar import CrmToolbar
from app.widgets.crm.customer_card import CustomerCard
from app.widgets.crm.followup_panel import FollowupPanel
from app.widgets.crm.pipeline_board import PipelineBoard


class CrmPage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CrmPage")
        self.controller = CrmController()
        self._customer_id = None
        self._deal_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.dashboard = CrmDashboard()
        layout.addWidget(self.dashboard)

        self.actions = CrmToolbar()
        self.search = self.actions.search
        layout.addWidget(self.actions)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("CrmTabs")

        self.board = PipelineBoard()
        self.customer_card = CustomerCard()
        self.activities = ActivityPanel()
        self.followup = FollowupPanel()

        split = QSplitter()
        split.setObjectName("CrmSplitter")
        split.addWidget(self.customer_card)
        split.addWidget(self.activities)
        split.setSizes([520, 360])

        self.tabs.addTab(self.board, "Pipeline")
        self.tabs.addTab(split, "Customer 360")
        self.tabs.addTab(self.followup, "Follow up")
        layout.addWidget(self.tabs, 1)

        self.actions.lead_clicked.connect(self.new_lead)
        self.actions.activity_clicked.connect(lambda: self.new_activity("Task"))
        self.actions.meeting_clicked.connect(lambda: self.new_activity("Meeting"))
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.export_clicked.connect(self.export_excel)
        self.actions.print_clicked.connect(self.print_pipeline)
        self.actions.filter_changed.connect(self.refresh)
        self.board.deal_moved.connect(self._move_deal)
        self.board.deal_selected.connect(self._select_deal)
        self.customer_card.customer_selected.connect(self._select_customer)
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.crm", splitters=[split], fields=[self.search])
        self.refresh()

    def refresh(self) -> None:
        self.actions.fill(
            self.controller.salespeople(),
            self.controller.statuses(),
            self.controller.stages(),
            self.controller.service.priorities(),
        )
        deals = self._deals()
        self.board.set_deals(deals)
        self.dashboard.set_kpis(self.controller.kpis())
        customers = self.controller.search_customers(self.search.text())
        self.customer_card.set_customers(customers)
        if self._customer_id:
            self._select_customer(self._customer_id)
        self.followup.set_followups(self.controller.followups())
        self.activities.set_activities(self.controller.repository.activities(self._customer_id))

    def new_lead(self) -> None:
        dialog = LeadDialog(self, self.controller)
        if dialog.exec():
            self.controller.create_lead(dialog.data())
            self.refresh()

    def new_activity(self, activity_type: str) -> None:
        dialog = ActivityDialog(
            self,
            self.controller,
            activity_type=activity_type,
            customer_id=self._customer_id,
            pipeline_id=self._deal_id,
        )
        if dialog.exec():
            self.controller.add_activity(dialog.data())
            self.refresh()

    def export_excel(self) -> None:
        start = str(self.controller.export_start_path())
        path, _ = QFileDialog.getSaveFileName(self, "Export", start, "Excel (*.xlsx)")
        if not path:
            return
        self.controller.export_excel(Path(path), self._deals())

    def print_pipeline(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        document = QTextDocument()
        document.setHtml(self.controller.print_html(self._deals()))
        document.print_(printer)

    def _deals(self) -> list:
        return self.controller.deals(
            query=self.search.text(),
            salesperson=self.actions.salesperson.currentData() or "all",
            status=self.actions.status.currentData() or "all",
            stage=self.actions.stage.currentData() or "all",
            priority=self.actions.priority.currentData() or "all",
            date_filter=self.actions.date_mode.currentData() or "all",
            selected_date=self.actions.date.date().toString("yyyy-MM-dd"),
        )

    def _move_deal(self, deal_id: int, stage: str) -> None:
        self.controller.set_stage(deal_id, stage)
        self.refresh()

    def _select_deal(self, deal_id: int) -> None:
        self._deal_id = deal_id
        deal = self.controller.repository.get_deal(deal_id)
        if deal and deal[1]:
            self._select_customer(int(deal[1]))

    def _select_customer(self, customer_id: int) -> None:
        self._customer_id = customer_id
        data = self.controller.customer_360(customer_id)
        self.customer_card.show_360(data)
        self.activities.set_activities(data.get("activities") or [])
