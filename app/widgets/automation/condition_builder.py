from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.modules.automation.automation_repository import CONDITION_FIELDS, OPERATORS


class ConditionBuilder(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._list = QVBoxLayout()
        layout.addLayout(self._list)
        add = QPushButton("Dodaj pogoj")
        add.setObjectName("SecondaryButton")
        add.setCursor(Qt.PointingHandCursor)
        add.setMinimumHeight(36)
        add.clicked.connect(lambda: self.add_row())
        layout.addWidget(add, alignment=Qt.AlignLeft)

    def add_row(self, data: dict | None = None) -> None:
        data = data or {}
        row = QWidget()
        box = QHBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        join_op = QComboBox()
        join_op.setObjectName("EnterpriseFilter")
        join_op.setMinimumHeight(36)
        join_op.addItem("AND", "AND")
        join_op.addItem("OR", "OR")
        join_op.setCurrentIndex(0 if (data.get("join_op") or "AND") == "AND" else 1)
        negate = QCheckBox("NOT")
        negate.setChecked(bool(data.get("negate")))
        field = QComboBox()
        field.setObjectName("EnterpriseFilter")
        field.setMinimumHeight(36)
        for key, title in CONDITION_FIELDS:
            field.addItem(title, key)
        idx = field.findData(data.get("field") or "invoice_total")
        field.setCurrentIndex(idx if idx >= 0 else 0)
        operator = QComboBox()
        operator.setObjectName("EnterpriseFilter")
        operator.setMinimumHeight(36)
        for key, title in OPERATORS:
            operator.addItem(title, key)
        op_idx = operator.findData(data.get("operator") or "gt")
        operator.setCurrentIndex(op_idx if op_idx >= 0 else 0)
        value = QLineEdit(str(data.get("value") or ""))
        value.setObjectName("EnterpriseInput")
        value.setPlaceholderText("vrednost ali izraz")
        value.setMinimumHeight(36)
        remove = QPushButton("Odstrani")
        remove.setObjectName("SecondaryButton")
        remove.setCursor(Qt.PointingHandCursor)
        remove.setMinimumHeight(36)
        widgets = {
            "join_op": join_op,
            "negate": negate,
            "field": field,
            "operator": operator,
            "value": value,
            "widget": row,
        }
        remove.clicked.connect(lambda: self._remove(widgets))
        for item in (join_op, negate, field, operator, value, remove):
            box.addWidget(item)
        self._list.addWidget(row)
        self._rows.append(widgets)

    def _remove(self, widgets: dict) -> None:
        self._rows = [item for item in self._rows if item is not widgets]
        widgets["widget"].setParent(None)

    def set_conditions(self, conditions: list[dict]) -> None:
        while self._rows:
            self._remove(self._rows[0])
        for item in conditions or []:
            self.add_row(item)

    def values(self) -> list[dict]:
        return [
            {
                "join_op": item["join_op"].currentData(),
                "negate": item["negate"].isChecked(),
                "field": item["field"].currentData(),
                "operator": item["operator"].currentData(),
                "value": item["value"].text().strip(),
            }
            for item in self._rows
        ]
