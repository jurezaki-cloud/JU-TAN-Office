"""Standardne velikosti in omejitve glede na zaslon."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHeaderView, QTableView

SIZE_PRESETS = {
    "SMALL": QSize(700, 520),
    "MEDIUM": QSize(980, 720),
    "LARGE": QSize(1200, 820),
    "XL": QSize(1400, 900),
}

# Začetna širina (spodnja meja), višina pride iz vsebine.
SIZE_MIN_WIDTH = {
    "SMALL": 520,
    "MEDIUM": 640,
    "LARGE": 760,
    "XL": 840,
}

MAX_WIDTH_RATIO = 0.90
MAX_HEIGHT_RATIO = 0.85
TABLE_MIN_HEIGHT = 88
TABLE_MAX_HEIGHT = 280
TABLE_EMPTY_ROWS = 2
TABLE_MAX_ROWS = 6
OUTER_MARGIN = 20
LAYOUT_SPACING = 12
FOOTER_HEIGHT = 48


def available_rect(widget=None) -> QRect:
    try:
        screen = None
        if widget is not None:
            screen = widget.screen()
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()
    except Exception:
        return QRect(0, 0, 1920, 1080)


def recommend_preset(rect: QRect | None = None) -> str:
    area = rect or available_rect()
    width, height = area.width(), area.height()
    if width <= 1440 or height <= 800:
        return "SMALL"
    if width <= 2048:
        return "MEDIUM"
    if width <= 3000:
        return "LARGE"
    return "XL"


def fit_size(preferred: QSize, available: QRect | None = None) -> QSize:
    """Omeji na 90 % × 85 % razpoložljivega zaslona, nikoli fullscreen."""
    area = available or available_rect()
    max_w = min(int(area.width() * MAX_WIDTH_RATIO), area.width() - 48)
    max_h = min(int(area.height() * MAX_HEIGHT_RATIO), area.height() - 48)
    width = min(max(preferred.width(), 320), max(320, max_w))
    height = min(max(preferred.height(), 240), max(240, max_h))
    if width >= area.width() or height >= area.height():
        width = min(width, area.width() - 48)
        height = min(height, area.height() - 48)
    return QSize(width, height)


def preset_size(name: str, widget=None) -> QSize:
    preferred = SIZE_PRESETS.get(name.upper(), SIZE_PRESETS["MEDIUM"])
    return fit_size(preferred, available_rect(widget))


def dialog_table_height(table: QTableView) -> int:
    """Višina tabele glede na število vrstic — prazna tabela ne zasede pol zaslona."""
    model = table.model()
    rows = int(model.rowCount()) if model is not None else 0
    header = table.horizontalHeader()
    header_h = header.sizeHint().height() or header.height() or 32
    row_h = table.verticalHeader().defaultSectionSize() or 40
    if rows <= 0:
        visible = TABLE_EMPTY_ROWS
    else:
        visible = min(max(rows, 1), TABLE_MAX_ROWS)
    height = int(header_h + visible * row_h + 8)
    return max(TABLE_MIN_HEIGHT, min(height, TABLE_MAX_HEIGHT))


def apply_dialog_table(table: QTableView) -> None:
    table.setAlternatingRowColors(True)
    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setSectionResizeMode(QHeaderView.Stretch)
    height = dialog_table_height(table)
    table.setMinimumHeight(height)
    table.setMaximumHeight(height)
    if not table.property("_jutan_row_size"):
        table.setProperty("_jutan_row_size", True)
        model = table.model()
        if model is not None:
            model.modelReset.connect(lambda: apply_dialog_table(table))
            model.rowsInserted.connect(lambda *_: apply_dialog_table(table))
            model.rowsRemoved.connect(lambda *_: apply_dialog_table(table))
