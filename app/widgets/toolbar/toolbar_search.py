from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit, QSizePolicy

from app.core.ui.brand_icons import brand_icon
from app.theme.colors import semantic_color
from app.theme.tokens import CONTROL_HEIGHT


class ToolbarSearch(QLineEdit):
    """Shell command-bar search — forwards to the active page filter when available."""

    query_changed = Signal(str)
    activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ToolbarSearch")
        self.setPlaceholderText("Išči v trenutnem modulu…")
        self.setClearButtonEnabled(True)
        self.setFixedHeight(CONTROL_HEIGHT)
        self.setMinimumWidth(160)
        self.setMaximumWidth(280)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setCursor(Qt.IBeamCursor)

        muted = semantic_color("TEXT_MUTED", "#64748B")
        self.addAction(brand_icon("search", color=muted, size=16), QLineEdit.LeadingPosition)

        self.textChanged.connect(self.query_changed.emit)
        self.returnPressed.connect(lambda: self.activated.emit(self.text().strip()))
