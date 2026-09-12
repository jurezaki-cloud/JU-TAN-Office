from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit


class ToolbarSearch(QLineEdit):
    query_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarSearch")
        self.setPlaceholderText("Išči v JU-TAN Office...")
        self.setClearButtonEnabled(True)
        self.textChanged.connect(self.query_changed.emit)
