from PySide6.QtCore import QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.theme.colors import LightColors


class PeriodFilterBar(QWidget):
    period_changed = Signal(str)
    custom_range_changed = Signal()

    OPTIONS = (
        ("Dan", "day"),
        ("Teden", "week"),
        ("Mesec", "month"),
        ("Leto", "year"),
        ("Po meri", "custom"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("AnalyticsFilterBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for label, key in self.OPTIONS:
            button = QPushButton(label)
            button.setObjectName("PeriodChip")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            button.setProperty("period", key)
            self.group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)

        self.from_date = QDateEdit()
        self.from_date.setObjectName("EnterpriseFilter")
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd. MM. yyyy")
        self.from_date.setMinimumHeight(36)

        self.to_date = QDateEdit()
        self.to_date.setObjectName("EnterpriseFilter")
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd. MM. yyyy")
        self.to_date.setMinimumHeight(36)

        from_label = QLabel("Od")
        from_label.setObjectName("DashboardMuted")
        to_label = QLabel("Do")
        to_label.setObjectName("DashboardMuted")

        layout.addSpacing(8)
        layout.addWidget(from_label)
        layout.addWidget(self.from_date)
        layout.addWidget(to_label)
        layout.addWidget(self.to_date)
        layout.addStretch()

        self._buttons["month"].setChecked(True)
        self._set_custom_enabled(False)

        self.group.buttonClicked.connect(self._on_clicked)
        self.from_date.dateChanged.connect(self._on_custom_dates)
        self.to_date.dateChanged.connect(self._on_custom_dates)

    def current_period(self) -> str:
        for key, button in self._buttons.items():
            if button.isChecked():
                return key
        return "month"

    def _on_clicked(self, button: QPushButton) -> None:
        period = button.property("period")
        self._set_custom_enabled(period == "custom")
        self.period_changed.emit(period)

    def _on_custom_dates(self, *_args) -> None:
        if self.current_period() == "custom":
            self.custom_range_changed.emit()

    def _set_custom_enabled(self, enabled: bool) -> None:
        self.from_date.setEnabled(enabled)
        self.to_date.setEnabled(enabled)


class ExportBar(QWidget):
    pdf_clicked = Signal()
    excel_clicked = Signal()
    print_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("AnalyticsExportBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.btn_pdf = QPushButton("Export PDF")
        self.btn_pdf.setObjectName("SecondaryButton")
        self.btn_excel = QPushButton("Export Excel")
        self.btn_excel.setObjectName("SecondaryButton")
        self.btn_print = QPushButton("Print")
        self.btn_print.setObjectName("PrimaryButton")

        for button in (self.btn_pdf, self.btn_excel, self.btn_print):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            layout.addWidget(button)

        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        self.btn_excel.clicked.connect(self.excel_clicked.emit)
        self.btn_print.clicked.connect(self.print_clicked.emit)


class RankingTable(QTableWidget):

    def __init__(self, headers: tuple[str, str], parent=None):
        super().__init__(0, 2, parent)

        self.setObjectName("EnterpriseTable")
        self.setHorizontalHeaderLabels(list(headers))
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setDefaultSectionSize(44)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMinimumHeight(280)

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        self.clearContents()
        self.setRowCount(len(rows) or 1)
        if not rows:
            empty = QTableWidgetItem("Ni podatkov")
            empty.setFlags(Qt.NoItemFlags)
            self.setItem(0, 0, empty)
            self.setSpan(0, 0, 1, 2)
            return
        self.clearSpans()
        for index, (name, value) in enumerate(rows):
            left = QTableWidgetItem(name)
            right = QTableWidgetItem(value)
            left.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            right.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            right.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(index, 0, left)
            self.setItem(index, 1, right)


class _ChartBase(QWidget):

    def __init__(self, object_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class LineChart(_ChartBase):

    def __init__(self, parent=None):
        super().__init__("AnalyticsLineChart", parent)
        self._points: list[tuple[str, float]] = []

    def set_points(self, points: list[tuple[str, float]]) -> None:
        self._points = list(points)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        points = self._points
        if not points:
            painter.end()
            return

        values = [float(value) for _, value in points]
        peak = max(values) if max(values) > 0 else 1.0
        left, top, right, bottom = 12, 16, 12, 28
        plot = QRect(
            left,
            top,
            max(1, self.width() - left - right),
            max(1, self.height() - top - bottom),
        )
        step = plot.width() / max(len(points) - 1, 1)
        coords = []
        for index, value in enumerate(values):
            x = plot.left() + step * index
            y = plot.bottom() - (value / peak) * (plot.height() - 8)
            coords.append((x, y))

        fill = QPainterPath()
        fill.moveTo(coords[0][0], plot.bottom())
        for x, y in coords:
            fill.lineTo(x, y)
        fill.lineTo(coords[-1][0], plot.bottom())
        fill.closeSubpath()
        brush = QColor(LightColors.PRIMARY)
        brush.setAlpha(40)
        painter.fillPath(fill, brush)

        pen = QPen(QColor(LightColors.PRIMARY))
        pen.setWidth(2)
        painter.setPen(pen)
        for index in range(1, len(coords)):
            x1, y1 = coords[index - 1]
            x2, y2 = coords[index]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setBrush(QColor(LightColors.PRIMARY))
        painter.setPen(Qt.NoPen)
        for x, y in coords:
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

        painter.setPen(QPen(QColor(LightColors.SECONDARY)))
        painter.setFont(QFont("Segoe UI", 8))
        stride = max(1, len(points) // 8)
        for index, (label, _) in enumerate(points):
            if index % stride != 0 and index != len(points) - 1:
                continue
            x = int(coords[index][0])
            painter.drawText(
                QRect(x - 18, plot.bottom() + 4, 36, 18),
                Qt.AlignHCenter | Qt.AlignTop,
                label,
            )
        painter.end()


class BarChart(_ChartBase):

    def __init__(self, parent=None):
        super().__init__("AnalyticsBarChart", parent)
        self._points: list[tuple[str, float]] = []

    def set_points(self, points: list[tuple[str, float]]) -> None:
        self._points = list(points)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        points = self._points
        if not points:
            painter.end()
            return

        values = [float(value) for _, value in points]
        peak = max(values) if max(values) > 0 else 1.0
        left, top, right, bottom = 8, 16, 8, 28
        plot = QRect(
            left,
            top,
            max(1, self.width() - left - right),
            max(1, self.height() - top - bottom),
        )
        bar_space = plot.width() / max(len(points), 1)
        bar_width = max(10, bar_space * 0.5)

        for index, (label, value) in enumerate(points):
            height = int((float(value) / peak) * (plot.height() - 8))
            x = int(plot.left() + bar_space * index + (bar_space - bar_width) / 2)
            y = plot.bottom() - height
            color = QColor(LightColors.PRIMARY)
            color.setAlpha(210)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(x, y, int(bar_width), max(4, height), 6, 6)
            painter.setPen(QPen(QColor(LightColors.SECONDARY)))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(
                QRect(x - 8, plot.bottom() + 4, int(bar_width) + 16, 18),
                Qt.AlignHCenter | Qt.AlignTop,
                label,
            )
        painter.end()


class PieChart(_ChartBase):

    PALETTE = (
        LightColors.PRIMARY,
        LightColors.SUCCESS,
        LightColors.WARNING,
        LightColors.DANGER,
        LightColors.SECONDARY,
    )

    def __init__(self, parent=None):
        super().__init__("AnalyticsPieChart", parent)
        self._slices: list[tuple[str, float]] = []

    def set_slices(self, slices: list[tuple[str, float]]) -> None:
        self._slices = list(slices)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        slices = [(name, float(value)) for name, value in self._slices if float(value) > 0]
        if not slices:
            painter.end()
            return

        total = sum(value for _, value in slices) or 1.0
        size = min(self.width() * 0.52, self.height() - 24)
        pie = QRectF(12, (self.height() - size) / 2, size, size)
        start = 90 * 16
        for index, (name, value) in enumerate(slices):
            span = int(round((value / total) * 360 * 16))
            color = QColor(self.PALETTE[index % len(self.PALETTE)])
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawPie(pie, start, -span)
            start -= span

        painter.setFont(QFont("Segoe UI", 9))
        legend_x = int(pie.right() + 16)
        y = int(max(16, pie.top()))
        for index, (name, value) in enumerate(slices):
            color = QColor(self.PALETTE[index % len(self.PALETTE)])
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(legend_x, y + 3, 10, 10, 3, 3)
            painter.setPen(QPen(QColor(LightColors.TEXT)))
            share = value / total * 100
            painter.drawText(
                QRect(legend_x + 16, y, max(80, self.width() - legend_x - 24), 18),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{name}  {share:.0f}%",
            )
            y += 22
        painter.end()
