from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.theme.colors import semantic_color

SLO_MONTHS = (
    "jan", "feb", "mar", "apr", "maj", "jun",
    "jul", "avg", "sep", "okt", "nov", "dec",
)


class RevenueChart(QWidget):
    """Stolpčni graf iz realnih mesečnih podatkov (prazno, če ni prometa)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("RevenueChart")
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._points: list[tuple[str, float]] = []

    def set_points(self, points: list[tuple[str, float]]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Antialiasing only when drawing bars — empty state is plain text.
        points = self._points
        if not points:
            painter.setPen(QPen(QColor(semantic_color("TEXT_MUTED", "#64748B"))))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Ni podatkov za graf")
            painter.end()
            return

        painter.setRenderHint(QPainter.Antialiasing)
        primary = QColor(semantic_color("PRIMARY", "#059669"))
        muted = QColor(semantic_color("TEXT_MUTED", "#64748B"))
        grid = QColor(semantic_color("BORDER", "#E2E8F0"))

        values = [float(v) for _, v in points]
        peak = max(values) if values and max(values) > 0 else 1.0

        left, top, right, bottom = 8, 16, 8, 28
        plot = QRect(
            left,
            top,
            max(1, self.width() - left - right),
            max(1, self.height() - top - bottom),
        )

        # Subtle baseline for enterprise polish
        painter.setPen(QPen(grid, 1))
        painter.drawLine(plot.left(), plot.bottom(), plot.right(), plot.bottom())

        bar_space = plot.width() / max(len(points), 1)
        bar_width = max(12, bar_space * 0.46)

        for index, (label, value) in enumerate(points):
            height = int((float(value) / peak) * (plot.height() - 8))
            x = int(plot.left() + bar_space * index + (bar_space - bar_width) / 2)
            y = plot.bottom() - height
            color = QColor(primary)
            color.setAlpha(210)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(x, y, int(bar_width), max(4, height), 6, 6)

            painter.setPen(QPen(muted))
            font = QFont("Segoe UI", 8)
            painter.setFont(font)
            painter.drawText(
                QRect(x - 8, plot.bottom() + 4, int(bar_width) + 16, 18),
                Qt.AlignHCenter | Qt.AlignTop,
                label,
            )

        painter.end()
