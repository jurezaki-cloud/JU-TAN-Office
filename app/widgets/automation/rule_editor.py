from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QSpinBox

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.modules.automation.automation_repository import SCHEDULE_KINDS
from app.widgets.automation.action_selector import ActionSelector
from app.widgets.automation.condition_builder import ConditionBuilder
from app.widgets.automation.trigger_selector import TriggerSelector
from app.widgets.cards.enterprise_card import EnterpriseCard


class RuleEditor(EnterpriseDialog):
    def __init__(self, parent=None, rule: dict | None = None) -> None:
        super().__init__(
            parent,
            title="Uredi pravilo" if rule else "Novo pravilo",
            heading="Visual Rule Builder",
            size="LARGE",
            state_key="dialog.rule",
        )
        self.setObjectName("RuleEditor")
        self._rule_id = rule.get("id") if rule else None

        meta = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.name = QLineEdit()
        self.name.setObjectName("EnterpriseInput")
        self.name.setMinimumHeight(36)
        self.description = QLineEdit()
        self.description.setObjectName("EnterpriseInput")
        self.description.setMinimumHeight(36)
        self.enabled = QCheckBox("Enable")
        self.enabled.setChecked(True)
        self.priority = QSpinBox()
        self.priority.setRange(1, 999)
        self.priority.setValue(100)
        self.priority.setMinimumHeight(36)
        self.priority.setObjectName("EnterpriseInput")
        self.schedule_kind = QComboBox()
        self.schedule_kind.setObjectName("EnterpriseFilter")
        self.schedule_kind.setMinimumHeight(36)
        for key, title in SCHEDULE_KINDS:
            self.schedule_kind.addItem(title, key)
        self.schedule_value = QLineEdit()
        self.schedule_value.setObjectName("EnterpriseInput")
        self.schedule_value.setPlaceholderText("09:00 | MON 09:00 | 1 09:00 | 0 9 * * *")
        self.schedule_value.setMinimumHeight(36)
        grid.add("Ime", self.name, "Opis", self.description)
        grid.add("Priority / order", self.priority, "Razpored", self.schedule_kind)
        grid.add("Vrednost", self.schedule_value)
        grid.add_span(self.enabled)
        meta.body.addLayout(grid.layout)
        self.body.addWidget(meta)

        trigger_card = EnterpriseCard("DashboardCard")
        trigger_title = QLabel("Trigger")
        trigger_title.setObjectName("SectionTitle")
        self.trigger = TriggerSelector()
        trigger_card.body.addWidget(trigger_title)
        trigger_card.body.addWidget(self.trigger)
        self.body.addWidget(trigger_card)

        cond_card = EnterpriseCard("DashboardCard")
        cond_title = QLabel("↓ Conditions (AND / OR / NOT)")
        cond_title.setObjectName("SectionTitle")
        self.conditions = ConditionBuilder()
        cond_card.body.addWidget(cond_title)
        cond_card.body.addWidget(self.conditions)
        self.body.addWidget(cond_card)

        action_card = EnterpriseCard("DashboardCard")
        action_title = QLabel("↓ Actions")
        action_title.setObjectName("SectionTitle")
        self.actions = ActionSelector()
        action_card.body.addWidget(action_title)
        action_card.body.addWidget(self.actions)
        self.body.addWidget(action_card)

        if rule:
            self.name.setText(rule.get("name") or "")
            self.description.setText(rule.get("description") or "")
            self.enabled.setChecked(bool(rule.get("enabled", True)))
            self.priority.setValue(int(rule.get("priority") or 100))
            kind = self.schedule_kind.findData(rule.get("schedule_kind") or "none")
            self.schedule_kind.setCurrentIndex(kind if kind >= 0 else 0)
            self.schedule_value.setText(rule.get("schedule_value") or "")
            self.trigger.set_value(rule.get("trigger_key") or "manual")
            self.conditions.set_conditions(rule.get("conditions") or [])
            self.actions.set_actions(rule.get("actions") or [])
        else:
            self.actions.add_row()

    def data(self) -> dict:
        return {
            "id": self._rule_id,
            "name": self.name.text().strip() or "Pravilo",
            "description": self.description.text().strip(),
            "trigger_key": self.trigger.value(),
            "enabled": self.enabled.isChecked(),
            "priority": self.priority.value(),
            "schedule_kind": self.schedule_kind.currentData(),
            "schedule_value": self.schedule_value.text().strip(),
            "conditions": self.conditions.values(),
            "actions": self.actions.values(),
        }
