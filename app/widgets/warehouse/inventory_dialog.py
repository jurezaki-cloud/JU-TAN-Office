from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.core.ui.sizes import apply_dialog_table
from app.modules.warehouse.warehouse_controller import WarehouseController
from app.widgets.cards.enterprise_card import EnterpriseCard


class InventoryDialog(EnterpriseDialog):

    def __init__(self, parent=None, controller: WarehouseController | None = None) -> None:
        super().__init__(
            parent,
            title="Inventura",
            heading="Inventura skladišča",
            size="MEDIUM",
            state_key="dialog.inventory",
            save_text="Potrdi inventuro",
        )
        self.controller = controller or WarehouseController()
        self.setObjectName("InventoryDialog")
        self.bind_save(self._save)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.warehouse = QComboBox()
        self.warehouse.setObjectName("EnterpriseFilter")
        self.warehouse.setMinimumHeight(36)
        for item in self.controller.warehouses():
            self.warehouse.addItem(item["name"], item["id"])
        self.user = QLineEdit(self.controller.default_user())
        self.user.setObjectName("EnterpriseSearch")
        self.user.setMinimumHeight(36)
        self.note = QLineEdit("Inventura")
        self.note.setObjectName("EnterpriseSearch")
        self.note.setMinimumHeight(36)
        grid.add("Skladišče", self.warehouse, "Uporabnik", self.user)
        grid.add("Opomba", self.note)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("EnterpriseTable")
        self.table.setHorizontalHeaderLabels(
            ["Šifra", "Naziv", "Na zalogi", "Preštej zalogo", "Razlika"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        apply_dialog_table(self.table)
        table_card.body.addWidget(self.table)
        self.body.addWidget(table_card)

        self.warehouse.currentIndexChanged.connect(self._reload)
        self._reload()

    def _reload(self) -> None:
        warehouse_id = self.warehouse.currentData()
        rows = self.controller.stock(warehouse_id=warehouse_id or "all")
        self.table.setRowCount(0)
        for row in rows:
            index = self.table.rowCount()
            self.table.insertRow(index)
            code = QTableWidgetItem(row.code)
            name = QTableWidgetItem(row.name)
            qty = QTableWidgetItem(_fmt(row.qty))
            diff = QTableWidgetItem("0")
            for item in (code, name, qty, diff):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            code.setData(Qt.UserRole, row.article_id)
            qty.setData(Qt.UserRole, row.qty)
            name.setData(Qt.UserRole, row.min_qty)
            self.table.setItem(index, 0, code)
            self.table.setItem(index, 1, name)
            self.table.setItem(index, 2, qty)
            spin = QDoubleSpinBox()
            spin.setObjectName("EnterpriseFilter")
            spin.setRange(0, 1_000_000)
            spin.setDecimals(2)
            spin.setValue(row.qty)
            spin.valueChanged.connect(lambda _value, r=index: self._update_diff(r))
            self.table.setCellWidget(index, 3, spin)
            self.table.setItem(index, 4, diff)

    def _update_diff(self, row: int) -> None:
        qty_item = self.table.item(row, 2)
        diff_item = self.table.item(row, 4)
        spin = self.table.cellWidget(row, 3)
        if qty_item is None or diff_item is None or spin is None:
            return
        current = float(qty_item.data(Qt.UserRole) or 0)
        delta = float(spin.value()) - current
        diff_item.setText(_fmt(delta))

    def _save(self) -> None:
        warehouse_id = str(self.warehouse.currentData() or "")
        counts = []
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0)
            name = self.table.item(row, 1)
            qty = self.table.item(row, 2)
            spin = self.table.cellWidget(row, 3)
            if code is None or qty is None or spin is None:
                continue
            counts.append({
                "article_id": int(code.data(Qt.UserRole)),
                "qty": float(qty.data(Qt.UserRole) or 0),
                "counted": float(spin.value()),
                "min_qty": float(name.data(Qt.UserRole) or 0) if name else 0,
            })
        self.controller.confirm_inventory(
            warehouse_id,
            counts,
            self.user.text().strip(),
            self.note.text().strip(),
        )
        self.accept()


def _fmt(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".replace(".", ",")
