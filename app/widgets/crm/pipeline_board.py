from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QScrollArea, QVBoxLayout, QWidget,
)

from app.modules.crm.crm_repository import STAGES
from app.utils.money import format_eur
from app.widgets.cards.enterprise_card import EnterpriseCard

STAGE_LABELS = {
    "Lead": "Novo",
    "Qualified": "Kontaktirano",
    "Proposal": "Ponudba",
    "Negotiation": "Pogajanja",
    "Won": "Dogovorjeno",
    "Lost": "Izgubljeno",
}
PRIORITY_LABELS = {
    "Low": "Nizka", "Normal": "Normalna", "High": "Visoka", "Urgent": "Nujna",
}


class StageColumn(QListWidget):
    deal_dropped = Signal(int, str)

    def __init__(self, stage: str, parent=None) -> None:
        super().__init__(parent)
        self.stage = stage
        self.setObjectName("CrmStageColumn")
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMinimumWidth(220)
        self.setSpacing(8)
        self.setWordWrap(True)

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
    deal_opened = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PipelineBoard")
        self.columns = {}
        self.headers = {}

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

        for stage in STAGES:
            card = EnterpriseCard("DashboardCard")
            title = QLabel(STAGE_LABELS.get(stage, stage))
            title.setObjectName("SectionTitle")
            meta = QLabel("0 priložnosti  ·  0,00 €")
            meta.setObjectName("KpiHint")
            column = StageColumn(stage)
            column.deal_dropped.connect(self.deal_moved.emit)
            column.itemClicked.connect(self._selected)
            column.itemDoubleClicked.connect(self._opened)
            card.body.addWidget(title)
            card.body.addWidget(meta)
            card.body.addWidget(column, 1)
            layout.addWidget(card)
            self.columns[stage] = column
            self.headers[stage] = meta

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def set_deals(self, deals: list) -> None:
        counts = {stage: 0 for stage in STAGES}
        totals = {stage: 0.0 for stage in STAGES}

        for column in self.columns.values():
            column.clear()

        for deal in deals:
            stage = deal[5] if deal[5] in self.columns else "Lead"
            value = float(deal[8] or 0)
            counts[stage] += 1
            totals[stage] += value
            priority = PRIORITY_LABELS.get(str(deal[7] or ""), str(deal[7] or ""))
            owner = str(deal[6] or "Brez skrbnika")
            item = QListWidgetItem(
                f"{deal[3]}\n"
                f"{deal[4] or 'Brez podjetja'}\n"
                f"{format_eur(value)}  ·  {priority}\n"
                f"Skrbnik: {owner}"
            )
            item.setData(Qt.UserRole, int(deal[0]))
            item.setToolTip("Povleci kartico v drugo fazo ali klikni za podrobnosti.")
            self.columns[stage].addItem(item)

        for stage in STAGES:
            noun = "priložnost" if counts[stage] == 1 else "priložnosti"
            self.headers[stage].setText(
                f"{counts[stage]} {noun}  ·  {format_eur(totals[stage])}"
            )

    def _selected(self, item: QListWidgetItem) -> None:
        self.deal_selected.emit(int(item.data(Qt.UserRole)))

    def _opened(self, item: QListWidgetItem) -> None:
        self.deal_opened.emit(int(item.data(Qt.UserRole)))
