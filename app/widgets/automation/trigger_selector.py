from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from app.modules.automation.automation_repository import TRIGGERS


class TriggerSelector(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Trigger")
        label.setObjectName("FieldLabel")
        self.combo = QComboBox()
        self.combo.setObjectName("EnterpriseFilter")
        self.combo.setMinimumHeight(36)
        for key, title in TRIGGERS:
            self.combo.addItem(title, key)
        layout.addWidget(label)
        layout.addWidget(self.combo, 1)

    def value(self) -> str:
        return self.combo.currentData() or "manual"

    def set_value(self, key: str) -> None:
        index = self.combo.findData(key)
        self.combo.setCurrentIndex(index if index >= 0 else 0)
