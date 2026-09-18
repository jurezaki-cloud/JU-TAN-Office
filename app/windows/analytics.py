from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFileDialog, QHeaderView, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.services.analytics_service import analytics_service
from app.services.report_export import export_business_report
from app.widgets.messages import show_error


class Analytics(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel("Analitika in poročila")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:8px;")
        self.btn_refresh = QPushButton("🔄 Osveži")
        self.btn_excel = QPushButton("📊 Izvozi Excel")
        top.addWidget(title); top.addStretch()
        top.addWidget(self.btn_refresh); top.addWidget(self.btn_excel)
        layout.addLayout(top)
        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.tabs.addTab(self.chart_view, "Mesečni prihodki")
        self.receivables_table = QTableWidget()
        self.receivables_table.setColumnCount(8)
        self.receivables_table.setHorizontalHeaderLabels([
            "Račun", "Stranka", "Izdano", "Zapade", "Skupaj", "Plačano",
            "Odprto", "Status",
        ])
        self.receivables_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.receivables_table, "Odprte terjatve")
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(4)
        self.customers_table.setHorizontalHeaderLabels([
            "Stranka", "Št. računov", "Fakturirano", "Plačano",
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabs.addTab(self.customers_table, "Najboljše stranke")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_excel.clicked.connect(self.export_excel)
        self.refresh()

    def refresh(self):
        try:
            monthly = analytics_service.monthly_revenue()
            bar_set = QBarSet("Prejeta plačila (€)")
            bar_set.append([amount for _, amount in monthly])
            series = QBarSeries(); series.append(bar_set)
            chart = QChart(); chart.addSeries(series)
            chart.setTitle("Prejeta plačila po mesecih")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            axis_x = QBarCategoryAxis(); axis_x.append([month for month, _ in monthly])
            axis_y = QValueAxis(); axis_y.setLabelFormat("%.2f €"); axis_y.setMin(0)
            maximum = max((amount for _, amount in monthly), default=0)
            axis_y.setMax(max(maximum * 1.15, 100))
            chart.addAxis(axis_x, Qt.AlignBottom); series.attachAxis(axis_x)
            chart.addAxis(axis_y, Qt.AlignLeft); series.attachAxis(axis_y)
            chart.legend().setVisible(False); self.chart_view.setChart(chart)

            receivables = analytics_service.receivables()
            self.receivables_table.setRowCount(len(receivables))
            for row_index, row in enumerate(receivables):
                values = [*row[:4], f"{row[4]:.2f} €", f"{row[5]:.2f} €",
                          f"{row[6]:.2f} €", row[7]]
                for column, value in enumerate(values):
                    self.receivables_table.setItem(
                        row_index, column, QTableWidgetItem(str(value))
                    )

            customers = analytics_service.top_customers()
            self.customers_table.setRowCount(len(customers))
            for row_index, row in enumerate(customers):
                values = [row[0], row[1], f"{row[2]:.2f} €", f"{row[3]:.2f} €"]
                for column, value in enumerate(values):
                    self.customers_table.setItem(
                        row_index, column, QTableWidgetItem(str(value))
                    )
        except Exception as error:
            show_error(self, error, "Analitike ni mogoče naložiti")

    def export_excel(self):
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Shrani poslovno poročilo", "JU-TAN-poslovno-porocilo.xlsx",
                "Excel dokumenti (*.xlsx)",
            )
            if not path:
                return
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            export_business_report(
                path, analytics_service.summary(), analytics_service.monthly_revenue(),
                analytics_service.receivables(), analytics_service.top_customers(),
            )
            QMessageBox.information(self, "Excel", "Poročilo je uspešno izvoženo.")
        except Exception as error:
            show_error(self, error, "Excel poročila ni mogoče ustvariti")
