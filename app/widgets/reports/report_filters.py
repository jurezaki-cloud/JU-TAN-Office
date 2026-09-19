from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QComboBox, QDateEdit, QHBoxLayout, QLabel, QSizePolicy, QWidget

from app.widgets.common.filter_controls import compact_filter


class ReportFiltersBar(QWidget):
    filter_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ReportFilters")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.date_from = QDateEdit()
        self.date_to = QDateEdit()
        today = QDate.currentDate()
        self.date_from.setDate(today.addMonths(-12))
        self.date_to.setDate(today)
        for widget in (self.date_from, self.date_to):
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd. MM. yyyy")
            compact_filter(widget)

        self.customer = QComboBox()
        self.supplier = QComboBox()
        self.salesperson = QComboBox()
        self.status = QComboBox()
        self.category = QComboBox()
        for combo in (self.customer, self.supplier, self.salesperson, self.status, self.category):
            compact_filter(combo)

        layout.addWidget(QLabel("Od"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("Do"))
        layout.addWidget(self.date_to)
        layout.addWidget(self.customer)
        layout.addWidget(self.supplier)
        layout.addWidget(self.salesperson)
        layout.addWidget(self.status)
        layout.addWidget(self.category)

        for widget in (self.date_from, self.date_to):
            widget.dateChanged.connect(lambda _: self.filter_changed.emit())
        for combo in (self.customer, self.supplier, self.salesperson, self.status, self.category):
            combo.currentIndexChanged.connect(lambda _: self.filter_changed.emit())

    def fill(self, options: dict) -> None:
        self._fill(self.customer, "Vse stranke", options.get("customers") or [])
        self._fill(self.supplier, "Vsi dobavitelji", options.get("suppliers") or [])
        self._fill(self.salesperson, "Vsi skrbniki", [(p, p) for p in options.get("salespeople") or []])
        self._fill(self.status, "Vsi statusi", [(s, s) for s in options.get("statuses") or []])
        self._fill(self.category, "Vse kategorije", [(c, c) for c in options.get("categories") or []])

    def _fill(self, combo: QComboBox, all_label: str, items: list) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label, "all")
        for key, label in items:
            combo.addItem(str(label), key)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
