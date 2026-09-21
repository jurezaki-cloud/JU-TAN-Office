from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
)

from app.theme.tokens import SPACE_2, SPACE_3, SPACE_4, TOOLBAR_HEIGHT
from app.widgets.toolbar.toolbar_actions import ToolbarActions
from app.widgets.toolbar.toolbar_search import ToolbarSearch
from app.widgets.toolbar.toolbar_title import ToolbarTitle
from app.widgets.toolbar.toolbar_user import ToolbarUser


class ModernToolbar(QFrame):
    """Shell command bar: page context · search · global actions."""

    new_invoice_clicked = Signal()
    new_offer_clicked = Signal()
    new_order_clicked = Signal()
    new_customer_clicked = Signal()
    settings_clicked = Signal()
    lock_clicked = Signal()
    search_changed = Signal(str)
    search_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ModernToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setFixedHeight(TOOLBAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACE_4, SPACE_2, SPACE_3, SPACE_2)
        layout.setSpacing(SPACE_3)

        self.title_block = ToolbarTitle()
        self.search = ToolbarSearch()
        self.actions = ToolbarActions()
        self.user = ToolbarUser()

        layout.addWidget(self.title_block, 1)
        layout.addWidget(self.search, 0)
        layout.addWidget(self.actions, 0)
        layout.addWidget(self.user, 0)

        self.actions.new_invoice_clicked.connect(self.new_invoice_clicked.emit)
        self.actions.new_offer_clicked.connect(self.new_offer_clicked.emit)
        self.actions.new_order_clicked.connect(self.new_order_clicked.emit)
        self.actions.new_customer_clicked.connect(self.new_customer_clicked.emit)
        self.actions.settings_clicked.connect(self.settings_clicked.emit)
        self.actions.lock_clicked.connect(self.lock_clicked.emit)
        self.search.query_changed.connect(self.search_changed.emit)
        self.search.activated.connect(self.search_activated.emit)

        self._page_index = 0
        self._compact = False

    def set_context(self, page_index: int) -> None:
        if page_index != self._page_index:
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)
            self._page_index = page_index
        self.title_block.set_context(page_index)
        self.actions.refresh_permissions()
        self.user.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep the command bar usable on constrained widths.
        compact = self.width() < 900
        if compact == self._compact:
            return
        self._compact = compact
        self.search.setVisible(not compact)
