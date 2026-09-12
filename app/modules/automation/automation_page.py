from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.errors import handle_error
from app.modules.automation.automation_controller import AutomationController
from app.widgets.automation.automation_table import AutomationTable
from app.widgets.automation.automation_toolbar import AutomationToolbar
from app.widgets.automation.execution_log_table import ExecutionLogTable
from app.widgets.automation.rule_editor import RuleEditor
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard


class AutomationPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AutomationPage")
        self.controller = AutomationController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Automation")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.kpi_rules = KpiCard("Pravila", "0")
        self.kpi_enabled = KpiCard("Omogočena", "0")
        self.kpi_runs = KpiCard("Zagona danes", "0")
        self.kpi_failed = KpiCard("Napake danes", "0")
        for card in (self.kpi_rules, self.kpi_enabled, self.kpi_runs, self.kpi_failed):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        self.actions = AutomationToolbar()
        self.search = self.actions.search
        layout.addWidget(self.actions)

        self.table = AutomationTable()
        self.log_table = ExecutionLogTable()
        rules_card = EnterpriseCard("DashboardCard")
        rules_title = QLabel("Business Rules")
        rules_title.setObjectName("SectionTitle")
        rules_card.body.addWidget(rules_title)
        rules_card.body.addWidget(self.table)
        log_card = EnterpriseCard("DashboardCard")
        log_title = QLabel("Execution Log")
        log_title.setObjectName("SectionTitle")
        log_card.body.addWidget(log_title)
        log_card.body.addWidget(self.log_table)

        split = QSplitter()
        split.setObjectName("AutomationSplitter")
        split.addWidget(rules_card)
        split.addWidget(log_card)
        split.setSizes([720, 480])
        layout.addWidget(split, 1)

        self.actions.new_clicked.connect(self.new_rule)
        self.actions.edit_clicked.connect(self.edit_rule)
        self.actions.delete_clicked.connect(self.delete_rule)
        self.actions.duplicate_clicked.connect(self.duplicate_rule)
        self.actions.enable_clicked.connect(lambda: self._enable(True))
        self.actions.disable_clicked.connect(lambda: self._enable(False))
        self.actions.run_clicked.connect(self.run_now)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.export_clicked.connect(self.export_excel)
        self.actions.filter_changed.connect(self.refresh)
        self.table.doubleClicked.connect(lambda *_: self.edit_rule())

        self._timer = QTimer(self)
        self._timer.setInterval(60_000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.automation", splitters=[split], tables=[self.table, self.log_table], fields=[self.search])
        self.refresh()

    def refresh(self) -> None:
        kpis = self.controller.kpis()
        self.kpi_rules.set_value(str(kpis["rules"]))
        self.kpi_enabled.set_value(str(kpis["enabled"]))
        self.kpi_runs.set_value(str(kpis["runs_today"]))
        self.kpi_failed.set_value(str(kpis["failed_today"]))
        rows = self.controller.rules(
            query=self.search.text(),
            trigger=self.actions.trigger.currentData() or "all",
            enabled=self.actions.enabled.currentData() or "all",
        )
        self.table.model_ref.refresh(rows)
        logs = self.controller.logs(
            query=self.search.text(),
            result=self.actions.log_result.currentData() or "all",
        )
        self.log_table.model_ref.refresh(logs)

    def new_rule(self) -> None:
        dialog = RuleEditor(self)
        if dialog.exec():
            self.controller.save(dialog.data())
            self.refresh()

    def edit_rule(self) -> None:
        rule_id = self.table.current_id()
        if rule_id is None:
            return
        rule = self.controller.get(rule_id)
        dialog = RuleEditor(self, rule)
        if dialog.exec():
            self.controller.save(dialog.data())
            self.refresh()

    def delete_rule(self) -> None:
        rule_id = self.table.current_id()
        if rule_id is None:
            return
        if QMessageBox.question(self, "Automation", "Izbrisati izbrano pravilo?") != QMessageBox.Yes:
            return
        self.controller.delete(rule_id)
        self.refresh()

    def duplicate_rule(self) -> None:
        rule_id = self.table.current_id()
        if rule_id is None:
            return
        self.controller.duplicate(rule_id)
        self.refresh()

    def _enable(self, enabled: bool) -> None:
        rule_id = self.table.current_id()
        if rule_id is None:
            return
        self.controller.set_enabled(rule_id, enabled)
        self.refresh()

    def run_now(self) -> None:
        rule_id = self.table.current_id()
        if rule_id is None:
            return
        try:
            result = self.controller.run_now(rule_id, {"trigger": "manual"})
            if result.get("result") == "failed":
                QMessageBox.warning(self, "Automation", result.get("error") or "Izvajanje ni uspelo.")
        except Exception as exc:
            handle_error(exc, context="automation-run", parent=self)
        self.refresh()

    def export_excel(self) -> None:
        start = str(self.controller.export_path())
        path, _ = QFileDialog.getSaveFileName(self, "Export", start, "Excel (*.xlsx)")
        if not path:
            return
        rows = self.controller.rules(
            query=self.search.text(),
            trigger=self.actions.trigger.currentData() or "all",
            enabled=self.actions.enabled.currentData() or "all",
        )
        self.controller.export_excel(Path(path), rows)

    def _tick(self) -> None:
        try:
            self.controller.tick()
        except Exception as exc:
            handle_error(exc, context="automation-tick")
        self.refresh()
