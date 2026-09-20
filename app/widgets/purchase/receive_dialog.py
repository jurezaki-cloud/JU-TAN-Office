from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.sizes import apply_dialog_table
from app.modules.purchase.purchase_controller import PurchaseController
from app.widgets.cards.enterprise_card import EnterpriseCard


class ReceiveDialog(EnterpriseDialog):

    def __init__(
        self,
        parent=None,
        controller: PurchaseController | None = None,
        purchase_id: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            title="Prevzem nabave",
            heading="Prevzem v skladišče",
            size="MEDIUM",
            state_key="dialog.receive",
            save_text="Potrdi prevzem",
        )
        self.controller = controller or PurchaseController()
        self.purchase_id = purchase_id
        self.setObjectName("ReceiveDialog")
        self.bind_save(self._save)

        card = EnterpriseCard("DashboardCard")
        card.body.setContentsMargins(8, 8, 8, 8)
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("EnterpriseTable")
        self.table.setHorizontalHeaderLabels(
            ["Artikel", "Naročeno", "Prevzeto", "Preostalo", "Prevzem zdaj"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        apply_dialog_table(self.table)
        card.body.addWidget(self.table)
        self.body.addWidget(card)

        self._load()

    def _load(self) -> None:
        self.table.setRowCount(0)
        for item in self.controller.items(self.purchase_id):
            ordered = float(item[4] or 0)
            received = float(item[5] or 0)
            remaining = max(ordered - received, 0)
            row = self.table.rowCount()
            self.table.insertRow(row)
            name = QTableWidgetItem(
                " — ".join(part for part in (str(item[2] or ""), str(item[3] or "")) if part)
            )
            name.setData(Qt.UserRole, int(item[0]))
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            qty = QTableWidgetItem(_fmt(ordered))
            done = QTableWidgetItem(_fmt(received))
            left = QTableWidgetItem(_fmt(remaining))
            for cell in (qty, done, left):
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, qty)
            self.table.setItem(row, 2, done)
            self.table.setItem(row, 3, left)
            spin = QDoubleSpinBox()
            spin.setObjectName("EnterpriseFilter")
            spin.setRange(0, remaining)
            spin.setDecimals(2)
            spin.setValue(remaining)
            self.table.setCellWidget(row, 4, spin)

    def _save(self) -> None:
        receipts = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0)
            spin = self.table.cellWidget(row, 4)
            if name is None or spin is None:
                continue
            receipts.append({
                "item_id": int(name.data(Qt.UserRole)),
                "qty": float(spin.value()),
            })
        self.controller.receive(self.purchase_id, receipts)
        self.accept()


def _fmt(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".replace(".", ",")
