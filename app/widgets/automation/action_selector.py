from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.modules.automation.automation_repository import ACTIONS


class ActionSelector(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[QComboBox, QLineEdit]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._list = QVBoxLayout()
        layout.addLayout(self._list)
        add = QPushButton("Dodaj akcijo")
        add.setObjectName("SecondaryButton")
        add.setCursor(Qt.PointingHandCursor)
        add.setMinimumHeight(36)
        add.clicked.connect(self.add_row)
        layout.addWidget(add, alignment=Qt.AlignLeft)
        self._layout = layout

    def add_row(self, action_key: str = "send_notification", config_text: str = "") -> None:
        row = QWidget()
        box = QHBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        combo = QComboBox()
        combo.setObjectName("EnterpriseFilter")
        combo.setMinimumHeight(36)
        for key, title in ACTIONS:
            combo.addItem(title, key)
        index = combo.findData(action_key)
        combo.setCurrentIndex(index if index >= 0 else 0)
        field = QLineEdit(config_text)
        field.setObjectName("EnterpriseInput")
        field.setPlaceholderText("config: message=..., status=..., total=...")
        field.setMinimumHeight(36)
        remove = QPushButton("Odstrani")
        remove.setObjectName("SecondaryButton")
        remove.setCursor(Qt.PointingHandCursor)
        remove.setMinimumHeight(36)
        remove.clicked.connect(lambda: self._remove(row, combo, field))
        box.addWidget(combo, 1)
        box.addWidget(field, 2)
        box.addWidget(remove)
        self._list.addWidget(row)
        self._rows.append((combo, field))

    def _remove(self, widget: QWidget, combo: QComboBox, field: QLineEdit) -> None:
        self._rows = [item for item in self._rows if item != (combo, field)]
        widget.setParent(None)

    def set_actions(self, actions: list[dict]) -> None:
        while self._rows:
            combo, field = self._rows[0]
            self._remove(combo.parentWidget(), combo, field)
        for action in actions or []:
            config = action.get("config") or {}
            text = ",".join(f"{key}={value}" for key, value in config.items())
            self.add_row(action.get("action_key") or "send_notification", text)
        if not actions:
            self.add_row()

    def values(self) -> list[dict]:
        items = []
        for combo, field in self._rows:
            config = {}
            for part in (field.text() or "").split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    config[key.strip()] = value.strip()
            items.append({"action_key": combo.currentData(), "config": config})
        return items
