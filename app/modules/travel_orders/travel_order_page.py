from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from openpyxl import Workbook

from app.core.ui.brand_icons import brand_icon
from app.database.travel_order_repository import travel_order_repository
from app.modules.travel_orders.travel_order_dialog import TravelOrderDialog
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard
from app.widgets.common.page_chrome import PageToolbar
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.invoices.status_badge import StatusBadgeDelegate
from app.widgets.offers.search_field import OfferSearch
from app.widgets.travel_orders.travel_order_table import TravelOrderTable
from PySide6.QtWidgets import QPushButton


class TravelOrderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TravelOrderPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Potni nalogi")
        title.setObjectName("PageTitle")
        title.hide()
        layout.addWidget(title)

        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.kpi_count = KpiCard("Potni nalogi", "0", "Aktivni")
        self.kpi_km = KpiCard("Kilometri", "0 km", "Prevoženo")
        self.kpi_total = KpiCard("Stroški", "0,00 €", "Brez storniranih")
        for card in (self.kpi_count, self.kpi_km, self.kpi_total):
            kpis.addWidget(card)
        layout.addLayout(kpis)

        toolbar = PageToolbar()
        self.search_field = OfferSearch()
        self.search_field.input.setPlaceholderText(
            "Išči številko, zaposlenega ali relacijo …"
        )
        self.search = self.search_field.input
        self.search.setMinimumWidth(260)

        self.filter = QComboBox()
        self.filter.setObjectName("EnterpriseFilter")
        self.filter.setMinimumHeight(34)
        self.filter.addItems(
            ["Vsi statusi", "Osnutek", "Odobren", "Zaključen", "Storniran"]
        )

        self.btn_new = QPushButton("Nov potni nalog")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setIcon(brand_icon("new", color="#FFFFFF", size=14))
        self.btn_edit = QPushButton("Odpri")
        self.btn_edit.setObjectName("SecondaryButton")
        self.btn_pdf = QPushButton("PDF")
        self.btn_pdf.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_cancel = QPushButton("Storniraj")
        self.btn_cancel.setObjectName("DangerButton")

        for button in (
            self.btn_new,
            self.btn_edit,
            self.btn_pdf,
            self.btn_excel,
            self.btn_cancel,
        ):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(34)

        toolbar.layout.addWidget(self.search_field, 1)
        toolbar.layout.addWidget(self.filter, 0)
        toolbar.layout.addWidget(self.btn_new, 0)
        toolbar.layout.addWidget(self.btn_edit, 0)
        toolbar.layout.addWidget(self.btn_pdf, 0)
        toolbar.layout.addWidget(self.btn_excel, 0)
        toolbar.layout.addWidget(self.btn_cancel, 0)
        layout.addWidget(toolbar)

        self.table = TravelOrderTable()
        self.table.setItemDelegateForColumn(7, StatusBadgeDelegate(self.table))

        table_card = EnterpriseCard("DashboardCard")
        table_card.body.setContentsMargins(8, 8, 8, 8)
        table_card.body.addWidget(self.table)

        self.empty_state = EmptyStateCard(
            "Ni potnih nalogov",
            "Ustvarite prvi potni nalog ali spremenite iskalni filter.",
            action_text="Nov potni nalog",
        )

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty_state)
        self.content_stack.addWidget(table_card)
        layout.addWidget(self.content_stack, 1)

        self.empty_state.action_clicked.connect(self.new_order)
        self.btn_new.clicked.connect(self.new_order)
        self.btn_edit.clicked.connect(self.edit_order)
        self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_excel.clicked.connect(self.export_excel)
        self.btn_cancel.clicked.connect(self.cancel_order)
        self.search.textChanged.connect(self.refresh)
        self.filter.currentTextChanged.connect(self.refresh)
        self.table.doubleClicked.connect(lambda _: self.edit_order())
        self.refresh()

    def _rows(self):
        rows = travel_order_repository.get_all()
        q = self.search.text().strip().lower()
        status = self.filter.currentText()
        if q:
            rows = [r for r in rows if q in f"{r[1]} {r[2]} {r[3]}".lower()]
        if status != "Vsi statusi":
            rows = [r for r in rows if (r[8] or "") == status]
        return rows

    def refresh(self, *_):
        all_rows = travel_order_repository.get_all()
        rows = self._rows()
        active = [r for r in all_rows if r[8] != "Storniran"]
        self.kpi_count.set_value(str(len(active)))
        self.kpi_km.set_value(
            f"{sum(float(r[6] or 0) for r in active):,.1f} km".replace(",", " ")
        )
        self.kpi_total.set_value(
            f"{sum(float(r[7] or 0) for r in active):,.2f} €".replace(",", " ")
        )
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for y, r in enumerate(rows):
            vals = (
                r[1],
                r[2],
                r[3],
                r[4] or "",
                r[5] or "",
                f"{float(r[6] or 0):.2f}",
                f"{float(r[7] or 0):.2f} €",
                r[8] or "",
            )
            for x, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.UserRole, r[0])
                if x in (5, 6):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(y, x, item)
        self.table.setSortingEnabled(True)
        if not rows:
            q = self.search.text().strip()
            status = self.filter.currentText()
            if q or status != "Vsi statusi":
                self.empty_state.set_message(
                    "Ni zadetkov",
                    "Poskusite z drugim iskanjem ali statusnim filtrom.",
                )
            else:
                self.empty_state.set_message(
                    "Ni potnih nalogov",
                    "Ustvarite prvi potni nalog ali spremenite iskalni filter.",
                )
            self.content_stack.setCurrentIndex(0)
        else:
            self.content_stack.setCurrentIndex(1)

    def selected_id(self):
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return None
        return self.table.item(row, 0).data(Qt.UserRole)

    def new_order(self):
        from app.core.permissions import allow

        if not allow("write", self):
            return
        if TravelOrderDialog(self).exec():
            self.refresh()

    def edit_order(self):
        oid = self.selected_id()
        if oid and TravelOrderDialog(self, oid).exec():
            self.refresh()

    def cancel_order(self):
        from app.core.permissions import allow, audit

        if not allow("write", self):
            return
        oid = self.selected_id()
        if oid and QMessageBox.question(
            self, "Storniranje", "Storniram izbrani potni nalog?"
        ) == QMessageBox.Yes:
            travel_order_repository.cancel(oid)
            audit("edit", f"travel_order:{oid}:cancelled")
            self.refresh()

    def export_pdf(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast_info
        from app.pdf.travel_order_pdf import export_travel_order

        if not allow("export", self):
            return
        oid = self.selected_id()
        if not oid:
            toast_info(self, "Najprej izberi potni nalog.")
            return
        path = export_travel_order(travel_order_repository.get_by_id(oid))
        audit("export", f"travel_order:{oid}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def export_excel(self):
        from app.core.permissions import allow, audit

        if not allow("export", self):
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel – potni nalogi", "potni-nalogi.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Potni nalogi"
        headers = [
            "Številka",
            "Zaposleni",
            "Relacija",
            "Odhod",
            "Prihod",
            "Km",
            "Skupaj",
            "Status",
        ]
        ws.append(headers)
        for r in self._rows():
            ws.append(
                [r[1], r[2], r[3], r[4], r[5], float(r[6] or 0), float(r[7] or 0), r[8]]
            )
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                40, max(12, max(len(str(c.value or "")) for c in col) + 2)
            )
        wb.save(Path(path))
        audit("export", "travel_orders:excel")
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
