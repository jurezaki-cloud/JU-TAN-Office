"""Shranjevanje geometrije, splitterjev in širin stolpcev."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QEvent, QObject, QRect
from PySide6.QtWidgets import QComboBox, QDateEdit, QLineEdit, QSplitter, QTableView, QWidget
from shiboken6 import isValid

from app.core.constants import DATA_DIR
from app.core.security import write_json_atomic

LAYOUT_PATH = DATA_DIR / "ui_layout.json"


def _load() -> dict:
    if not LAYOUT_PATH.exists():
        return {}
    try:
        import json
        data = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    write_json_atomic(LAYOUT_PATH, data)


def _encode(raw: QByteArray) -> str:
    return bytes(raw.toBase64()).decode("ascii")


def _decode(text: str) -> QByteArray:
    return QByteArray.fromBase64(str(text or "").encode("ascii"))


class LayoutMemory(QObject):
    def __init__(
        self,
        host: QWidget,
        key: str,
        *,
        splitters: list[QSplitter] | None = None,
        tables: list[QTableView] | None = None,
        fields: list[QWidget] | None = None,
        geometry: bool = False,
    ) -> None:
        super().__init__(host)
        self.host = host
        self.key = key
        self.splitters = list(splitters or [])
        self.tables = list(tables or [])
        self.fields = list(fields or [])
        self.geometry = geometry
        host.installEventFilter(self)

    def eventFilter(self, obj, event):
        host = getattr(self, "host", None)
        if host is not None and obj is host:
            if event.type() == QEvent.Show:
                self.restore()
            elif event.type() in (QEvent.Hide, QEvent.Close):
                self.persist()
        try:
            return super().eventFilter(obj, event)
        except Exception:
            return False

    def persist(self) -> None:
        try:
            if not isValid(self.host):
                return
            data = _load()
            entry = data.get(self.key) or {}
            if self.geometry:
                geo = self.host.geometry()
                if geo.width() >= 400 and geo.height() >= 300:
                    entry["x"] = geo.x()
                    entry["y"] = geo.y()
                    entry["w"] = geo.width()
                    entry["h"] = geo.height()
            entry["splitters"] = [
                _encode(item.saveState()) for item in self.splitters if isValid(item)
            ]
            columns = []
            sorts = []
            for table in self.tables:
                if not isValid(table):
                    continue
                header = table.horizontalHeader()
                columns.append([header.sectionSize(i) for i in range(header.count())])
                sorts.append([header.sortIndicatorSection(), int(header.sortIndicatorOrder())])
            entry["columns"] = columns
            entry["sort"] = sorts
            filters = []
            for field in self.fields:
                if not isValid(field):
                    continue
                if isinstance(field, QLineEdit):
                    filters.append({"t": "edit", "v": field.text()})
                elif isinstance(field, QComboBox):
                    filters.append({"t": "combo", "v": field.currentIndex()})
                elif isinstance(field, QDateEdit):
                    filters.append({"t": "date", "v": field.date().toString("yyyy-MM-dd")})
            if filters:
                entry["filters"] = filters
            data[self.key] = entry
            _save(data)
        except Exception:
            pass

    def restore(self) -> None:
        try:
            if not isValid(self.host):
                return
            entry = (_load().get(self.key) or {})
        except Exception:
            return
        if self.geometry and {"x", "y", "w", "h"} <= entry.keys():
            try:
                rect = QRect(int(entry["x"]), int(entry["y"]), int(entry["w"]), int(entry["h"]))
                screen = self.host.screen().availableGeometry() if self.host.screen() else None
                if screen is not None and screen.intersects(rect) and rect.width() >= 400 and rect.height() >= 300:
                    self.host.setGeometry(rect)
            except Exception:
                pass
        try:
            for splitter, raw in zip(self.splitters, entry.get("splitters") or []):
                splitter.restoreState(_decode(raw))
            for table, widths in zip(self.tables, entry.get("columns") or []):
                header = table.horizontalHeader()
                for index, width in enumerate(widths):
                    if 0 <= index < header.count() and int(width) > 24:
                        header.resizeSection(index, int(width))
            for table, sort in zip(self.tables, entry.get("sort") or []):
                if not isValid(table) or not table.isSortingEnabled():
                    continue
                section, order = int(sort[0]), int(sort[1])
                model = table.model()
                if model is None or not (0 <= section < model.columnCount()):
                    continue
                table.sortByColumn(section, order)
            from PySide6.QtCore import QDate
            for field, payload in zip(self.fields, entry.get("filters") or []):
                if not isValid(field) or not isinstance(payload, dict):
                    continue
                kind, value = payload.get("t"), payload.get("v")
                if kind == "edit" and isinstance(field, QLineEdit):
                    field.setText(str(value or ""))
                elif kind == "combo" and isinstance(field, QComboBox):
                    index = int(value)
                    if 0 <= index < field.count():
                        field.setCurrentIndex(index)
                elif kind == "date" and isinstance(field, QDateEdit):
                    date = QDate.fromString(str(value), "yyyy-MM-dd")
                    if date.isValid():
                        field.setDate(date)
        except Exception:
            pass


def remember_layout(
    host: QWidget,
    key: str,
    *,
    splitters: list[QSplitter] | None = None,
    tables: list[QTableView] | None = None,
    fields: list[QWidget] | None = None,
    geometry: bool = False,
) -> LayoutMemory:
    return LayoutMemory(
        host, key, splitters=splitters, tables=tables, fields=fields, geometry=geometry
    )
