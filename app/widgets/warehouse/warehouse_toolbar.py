from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.theme.colors import LightColors


def _search_icon() -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(LightColors.SECONDARY))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawEllipse(2, 2, 10, 10)
    painter.drawLine(11, 11, 16, 16)
    painter.end()
    return QIcon(pixmap)


class WarehouseToolbar(QWidget):
    movement_clicked = Signal()
    inventory_clicked = Signal()
    refresh_clicked = Signal()
    excel_clicked = Signal()
    print_clicked = Signal()
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("WarehouseToolbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setObjectName("EnterpriseSearch")
        self.search.setPlaceholderText("Išči po šifri, nazivu ali skladišču...")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(36)
        self.search.setMinimumWidth(220)
        self.search.addAction(_search_icon(), QLineEdit.LeadingPosition)

        self.warehouse = QComboBox()
        self.status = QComboBox()
        self.category = QComboBox()
        for combo in (self.warehouse, self.status, self.category):
            combo.setObjectName("EnterpriseFilter")
            combo.setMinimumHeight(36)

        self.btn_movement = QPushButton("+ Novo gibanje")
        self.btn_movement.setObjectName("PrimaryButton")
        self.btn_inventory = QPushButton("Inventura")
        self.btn_inventory.setObjectName("SecondaryButton")
        self.btn_refresh = QPushButton("Osveži")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Export Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("SecondaryButton")

        layout.addWidget(self.search)
        layout.addWidget(self.warehouse)
        layout.addWidget(self.status)
        layout.addWidget(self.category)
        for button in (
            self.btn_movement,
            self.btn_inventory,
            self.btn_refresh,
            self.btn_excel,
            self.btn_print,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_movement.clicked.connect(self.movement_clicked.emit)
        self.btn_inventory.clicked.connect(self.inventory_clicked.emit)
        self.btn_refresh.clicked.connect(self.refresh_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_print.clicked.connect(self.print_clicked.emit)
        self.search.textChanged.connect(lambda _: self.filter_changed.emit())
        self.warehouse.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.status.currentIndexChanged.connect(lambda _: self.filter_changed.emit())
        self.category.currentIndexChanged.connect(lambda _: self.filter_changed.emit())

    def fill_filters(
        self,
        warehouses: list[dict[str, str]],
        statuses: tuple[tuple[str, str], ...],
        categories: list[str],
    ) -> None:
        self._refill(self.warehouse, [("all", "Vsa skladišča")] + [
            (item["id"], item["name"]) for item in warehouses
        ])
        self._refill(self.status, list(statuses))
        self._refill(
            self.category,
            [("all", "Vse kategorije")] + [(item, item) for item in categories],
        )

    def warehouse_id(self) -> str:
        return self.warehouse.currentData() or "all"

    def status_value(self) -> str:
        return self.status.currentData() or "all"

    def category_value(self) -> str:
        return self.category.currentData() or "all"

    @staticmethod
    def _refill(combo: QComboBox, items: list[tuple[str, str]]) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for key, label in items:
            combo.addItem(label, key)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
