from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
)

from app.theme.tokens import TOOLBAR_HEIGHT
from app.widgets.toolbar.toolbar_actions import ToolbarActions
from app.widgets.toolbar.toolbar_title import ToolbarTitle
from app.widgets.toolbar.toolbar_user import ToolbarUser


class ModernToolbar(QFrame):
    """Shell command bar: page context (left) + global actions (right)."""

    new_invoice_clicked = Signal()
    new_offer_clicked = Signal()
    new_order_clicked = Signal()
    new_customer_clicked = Signal()
    settings_clicked = Signal()
    lock_clicked = Signal()
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ModernToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFixedHeight(TOOLBAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 12, 6)
        layout.setSpacing(10)

        self.title_block = ToolbarTitle()
        self.actions = ToolbarActions()
        self.user = ToolbarUser()

        layout.addWidget(self.title_block, 1)
        layout.addWidget(self.actions, 0)
        layout.addWidget(self.user, 0)

        self.actions.new_invoice_clicked.connect(self.new_invoice_clicked.emit)
        self.actions.new_offer_clicked.connect(self.new_offer_clicked.emit)
        self.actions.new_order_clicked.connect(self.new_order_clicked.emit)
        self.actions.new_customer_clicked.connect(self.new_customer_clicked.emit)
        self.actions.settings_clicked.connect(self.settings_clicked.emit)
        self.actions.lock_clicked.connect(self.lock_clicked.emit)

    def set_context(self, page_index: int) -> None:
        self.title_block.set_context(page_index)
        self.actions.refresh_permissions()
        self.user.refresh()
