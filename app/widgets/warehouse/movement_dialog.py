from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QTextEdit

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.article_repository import article_repository
from app.modules.warehouse.warehouse_controller import WarehouseController
from app.widgets.cards.enterprise_card import EnterpriseCard


class MovementDialog(EnterpriseDialog):

    def __init__(
        self,
        parent=None,
        controller: WarehouseController | None = None,
        article_id: int | None = None,
        warehouse_id: str | None = None,
    ) -> None:
        super().__init__(
            parent,
            title="Novo gibanje",
            heading="Zabeleži gibanje zaloge",
            size="SMALL",
            state_key="dialog.movement",
            save_text="Potrdi",
        )
        self.controller = controller or WarehouseController()
        self.setObjectName("MovementDialog")
        self.bind_save(self._save)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.article = QComboBox()
        self.warehouse = QComboBox()
        self.movement_type = QComboBox()
        for combo in (self.article, self.warehouse, self.movement_type):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)

        for article in article_repository.get_all():
            label = " — ".join(part for part in (str(article[1] or ""), str(article[2] or "")) if part)
            self.article.addItem(label or f"#{article[0]}", int(article[0]))
        for item in self.controller.warehouses():
            self.warehouse.addItem(item["name"], item["id"])
        for item in self.controller.movement_types():
            self.movement_type.addItem(item, item)

        if article_id is not None:
            index = self.article.findData(article_id)
            if index >= 0:
                self.article.setCurrentIndex(index)
        if warehouse_id and warehouse_id != "all":
            index = self.warehouse.findData(warehouse_id)
            if index >= 0:
                self.warehouse.setCurrentIndex(index)

        self.quantity = QDoubleSpinBox()
        self.quantity.setObjectName("EnterpriseFilter")
        self.quantity.setRange(-1_000_000, 1_000_000)
        self.quantity.setDecimals(2)
        self.quantity.setValue(1)
        self.quantity.setMinimumHeight(36)
        self.min_qty = QDoubleSpinBox()
        self.min_qty.setObjectName("EnterpriseFilter")
        self.min_qty.setRange(0, 1_000_000)
        self.min_qty.setDecimals(2)
        self.min_qty.setMinimumHeight(36)
        self.user = QLineEdit(self.controller.default_user())
        self.user.setObjectName("EnterpriseSearch")
        self.user.setMinimumHeight(36)
        self.note = QTextEdit()
        self.note.setPlaceholderText("Opomba")
        self.note.setMinimumHeight(72)
        self.note.setMaximumHeight(120)

        grid.add("Artikel", self.article, "Skladišče", self.warehouse)
        grid.add("Tip", self.movement_type, "Količina", self.quantity)
        grid.add("Minimalna zaloga", self.min_qty, "Uporabnik", self.user)
        grid.add_full("Opomba", self.note)
        card.body.addLayout(grid.layout)
        self.body.addWidget(card)

    def _save(self) -> None:
        if self.article.count() == 0:
            self.reject()
            return
        movement_type = self.movement_type.currentData()
        min_value = float(self.min_qty.value())
        min_qty = min_value if min_value > 0 or movement_type == "Korekcija" else None
        self.controller.add_movement(
            movement_type=movement_type,
            article_id=int(self.article.currentData()),
            warehouse_id=str(self.warehouse.currentData()),
            quantity=float(self.quantity.value()),
            user=self.user.text().strip(),
            note=self.note.toPlainText().strip(),
            min_qty=min_qty,
        )
        self.accept()
