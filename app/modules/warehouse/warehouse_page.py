from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.notify import toast
from app.modules.warehouse.models.movement_table_model import MovementTableModel
from app.modules.warehouse.models.stock_table_model import StockTableModel
from app.modules.warehouse.warehouse_controller import WarehouseController
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.warehouse.inventory_dialog import InventoryDialog
from app.widgets.warehouse.movement_dialog import MovementDialog
from app.widgets.warehouse.stock_card import StockCard
from app.widgets.warehouse.stock_table import StockTable
from app.widgets.warehouse.warehouse_toolbar import WarehouseToolbar


class WarehousePage(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setObjectName("WarehousePage")
        self.controller = WarehouseController()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Skladišče")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(16)
        self.kpi_articles = KpiCard("Skupno artiklov", "0", "Katalog")
        self.kpi_in_stock = KpiCard("Artikli na zalogi", "0", "Količina > 0")
        self.kpi_low = KpiCard("Artikli pod minimalno zalogo", "0", "Pod pragom")
        self.kpi_reserved = KpiCard("Rezervirani artikli", "0", "Rezervacija > 0")
        self.kpi_value = KpiCard("Skupna vrednost zaloge", "0,00 €", "Zaloga × cena")
        for card in (
            self.kpi_articles,
            self.kpi_in_stock,
            self.kpi_low,
            self.kpi_reserved,
            self.kpi_value,
        ):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        self.actions = WarehouseToolbar()
        self.search = self.actions.search
        layout.addWidget(self.actions)

        self.table = StockTable()
        self.model = StockTableModel()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(7, StatusBadgeDelegate(self.table))

        self.details = StockCard()

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        stock_split = QSplitter()
        stock_split.setObjectName("WarehouseSplitter")
        stock_split.addWidget(table_card)
        stock_split.addWidget(self.details)
        stock_split.setSizes([860, 280])
        stock_split.setChildrenCollapsible(False)

        self.movements = StockTable()
        self.movement_model = MovementTableModel()
        self.movements.setModel(self.movement_model)
        self.movements.setItemDelegateForColumn(1, StatusBadgeDelegate(self.movements))

        movement_card = EnterpriseCard("DashboardCard")
        movement_heading = QLabel("Gibanja")
        movement_heading.setObjectName("SectionTitle")
        movement_card.body.addWidget(movement_heading)
        movement_card.body.setContentsMargins(8, 8, 8, 8)
        movement_card.body.addWidget(self.movements)

        splitter = QSplitter()
        splitter.setObjectName("WarehouseMainSplitter")
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(stock_split)
        splitter.addWidget(movement_card)
        splitter.setSizes([520, 260])
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        self.actions.movement_clicked.connect(self.new_movement)
        self.actions.inventory_clicked.connect(self.run_inventory)
        self.actions.refresh_clicked.connect(self.refresh)
        self.actions.excel_clicked.connect(self.export_excel)
        self.actions.print_clicked.connect(self.print_stock)
        self.actions.filter_changed.connect(self.refresh)
        self.table.clicked.connect(self._show_details)
        self.table.doubleClicked.connect(lambda _: self.new_movement())
        self.table.selectionModel().selectionChanged.connect(self._show_details)

        from app.core.ui.window_state import remember_layout
        remember_layout(
            self,
            "page.warehouse",
            splitters=[stock_split, splitter],
            tables=[self.table, self.movements],
            fields=[self.search, self.actions.warehouse, self.actions.status, self.actions.category],
        )
        self.refresh()

    def refresh(self, reload_filters: bool = False) -> None:
        if reload_filters or self.actions.warehouse.count() == 0:
            self.actions.fill_filters(
                self.controller.warehouses(),
                self.controller.status_options(),
                self.controller.categories(),
            )
        rows = self.controller.stock(
            query=self.search.text(),
            warehouse_id=self.actions.warehouse_id(),
            status=self.actions.status_value(),
            category=self.actions.category_value(),
        )
        self.model.refresh(rows)
        self.movement_model.refresh(self.controller.movements())
        self._update_kpis()
        self._show_details()

    def new_movement(self) -> None:
        if not self.controller.stock():
            QMessageBox.information(
                self,
                "Skladišče",
                "Najprej dodajte artikel v katalog.",
            )
            return
        selected = self._selected_row()
        dialog = MovementDialog(
            self,
            self.controller,
            article_id=selected.article_id if selected else None,
            warehouse_id=selected.warehouse_id if selected else self.actions.warehouse_id(),
        )
        if dialog.exec():
            self.refresh(reload_filters=True)

    def run_inventory(self) -> None:
        dialog = InventoryDialog(self, self.controller)
        if dialog.exec():
            self.refresh(reload_filters=True)

    def export_excel(self) -> None:
        start = str(self.controller.export_start_path())
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Excel izvoz",
            start,
            "Excel (*.xlsx)",
        )
        if not path:
            return
        self.controller.export_excel(Path(path), self.model.rows)
        toast(self, "Excel izvožen")

    def print_stock(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        document = QTextDocument()
        document.setHtml(self._print_html())
        document.print_(printer)

    def _print_html(self) -> str:
        rows = "".join(
            "<tr>"
            f"<td>{escape(row.code)}</td>"
            f"<td>{escape(row.name)}</td>"
            f"<td>{escape(row.warehouse)}</td>"
            f"<td>{row.qty}</td>"
            f"<td>{row.reserved}</td>"
            f"<td>{row.free}</td>"
            f"<td>{row.min_qty}</td>"
            f"<td>{escape(row.status)}</td>"
            "</tr>"
            for row in self.model.rows
        )
        return (
            "<h2>Skladišče — zaloga</h2>"
            "<table border='1' cellspacing='0' cellpadding='6'>"
            "<tr><th>Šifra</th><th>Naziv</th><th>Skladišče</th>"
            "<th>Na zalogi</th><th>Rezervirano</th><th>Prosto</th>"
            "<th>Minimalna zaloga</th><th>Status</th></tr>"
            f"{rows}</table>"
        )

    def _selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.row_at(indexes[0].row())

    def _show_details(self, *_args) -> None:
        self.details.load(self._selected_row())

    def _update_kpis(self) -> None:
        kpis = self.controller.kpis()
        self.kpi_articles.set_value(str(kpis["articles"]))
        self.kpi_in_stock.set_value(str(kpis["in_stock"]))
        self.kpi_low.set_value(str(kpis["low_stock"]))
        self.kpi_reserved.set_value(str(kpis["reserved"]))
        value = float(kpis["value"])
        self.kpi_value.set_value(f"{value:,.2f} €".replace(",", " "))
