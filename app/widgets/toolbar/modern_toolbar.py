from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QSizePolicy,
)

from app.theme.colors import LightColors
from app.widgets.toolbar.toolbar_actions import ToolbarActions
from app.widgets.toolbar.toolbar_search import ToolbarSearch
from app.widgets.toolbar.toolbar_title import ToolbarTitle
from app.widgets.toolbar.toolbar_user import ToolbarUser


class ModernToolbar(QFrame):
    new_invoice_clicked = Signal()
    new_customer_clicked = Signal()
    settings_clicked = Signal()
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ModernToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        self.title_block = ToolbarTitle()
        self.search = ToolbarSearch()
        self.search.setMinimumWidth(280)
        self.search.setMaximumWidth(420)
        self.actions = ToolbarActions()
        self.user = ToolbarUser()

        layout.addWidget(self.title_block, 0)
        layout.addStretch(1)
        layout.addWidget(self.search, 0)
        layout.addStretch(1)
        layout.addWidget(self.actions, 0)
        layout.addWidget(self.user, 0)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 2)
        color = QColor(LightColors.TEXT)
        color.setAlpha(28)
        shadow.setColor(color)
        self.setGraphicsEffect(shadow)

        self.actions.new_invoice_clicked.connect(self.new_invoice_clicked.emit)
        self.actions.new_customer_clicked.connect(self.new_customer_clicked.emit)
        self.actions.settings_clicked.connect(self.settings_clicked.emit)
        self.search.query_changed.connect(self.search_changed.emit)

    def set_context(self, page_index: int) -> None:
        self.title_block.set_context(page_index)
