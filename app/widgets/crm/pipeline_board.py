from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QMimeData
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class StageColumn(QListWidget):
    deal_dropped = Signal(int, str)

    def __init__(self, stage: str, parent=None) -> None:
        super().__init__(parent)
        self.stage = stage
        self.setObjectName("EnterpriseTable")
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMinimumWidth(180)
        self.setSpacing(6)

    def startDrag(self, supported_actions) -> None:
        item = self.currentItem()
        if item is None:
            return
        mime = QMimeData()
        mime.setText(str(item.data(Qt.UserRole)))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        try:
            deal_id = int(event.mimeData().text())
        except (TypeError, ValueError):
            return
        event.acceptProposedAction()
        self.deal_dropped.emit(deal_id, self.stage)


class PipelineBoard(QWidget):
    deal_moved = Signal(int, str)
    deal_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PipelineBoard")
        self.columns: dict[str, StageColumn] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("CrmPipelineScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        layout = QHBoxLayout(inner)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        from app.modules.crm.crm_repository import STAGES

        for stage in STAGES:
            card = EnterpriseCard("DashboardCard")
            title = QLabel(stage)
            title.setObjectName("SectionTitle")
            column = StageColumn(stage)
            column.deal_dropped.connect(self.deal_moved.emit)
            column.itemClicked.connect(self._selected)
            card.body.addWidget(title)
            card.body.addWidget(column, 1)
            layout.addWidget(card)
            self.columns[stage] = column

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def set_deals(self, deals: list) -> None:
        for column in self.columns.values():
            column.clear()
        for deal in deals:
            stage = deal[5] if deal[5] in self.columns else "Lead"
            item = QListWidgetItem(
                f"{deal[3]}\n{deal[4] or '—'}\n{_money(deal[8])} · {deal[7]}"
            )
            item.setData(Qt.UserRole, int(deal[0]))
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            self.columns[stage].addItem(item)

    def _selected(self, item: QListWidgetItem) -> None:
        self.deal_selected.emit(int(item.data(Qt.UserRole)))


def _money(value) -> str:
    try:
        return f"{float(value or 0):,.2f} €".replace(",", " ")
    except (TypeError, ValueError):
        return "0.00 €"
