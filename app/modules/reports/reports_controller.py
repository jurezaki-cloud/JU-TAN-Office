from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QThread, Signal

from app.modules.reports.reporting_service import (
    PAGE_SIZE,
    ReportFilters,
    ReportResult,
    reporting_service,
)


class ReportWorker(QThread):
    loaded = Signal(object)
    failed = Signal(str)

    def __init__(self, key: str, filters: ReportFilters, parent=None) -> None:
        super().__init__(parent)
        self.key = key
        self.filters = filters

    def run(self) -> None:
        try:
            self.loaded.emit(reporting_service.run(self.key, self.filters))
        except Exception as exc:
            self.failed.emit(str(exc))


class ReportsController:
    def __init__(self) -> None:
        self.service = reporting_service
        self.page = 0
        self.result: ReportResult | None = None
        self._worker: ReportWorker | None = None

    def options(self) -> dict:
        return self.service.filter_options()

    def load(self, key: str, filters: ReportFilters, on_ok, on_err, parent=None) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
        self.page = 0
        worker = ReportWorker(key, filters, parent)
        worker.loaded.connect(lambda result: self._done(result, on_ok))
        worker.failed.connect(on_err)
        self._worker = worker
        worker.start()

    def _done(self, result: ReportResult, on_ok) -> None:
        self.result = result
        self.page = 0
        on_ok(result)

    def visible_rows(self) -> list:
        if self.result is None:
            return []
        end = (self.page + 1) * PAGE_SIZE
        return self.result.rows[:end]

    def has_more(self) -> bool:
        if self.result is None:
            return False
        return len(self.result.rows) > (self.page + 1) * PAGE_SIZE

    def more(self) -> None:
        if self.has_more():
            self.page += 1

    def filters_from(
        self,
        date_from: QDate,
        date_to: QDate,
        customer_id,
        supplier_id,
        salesperson: str,
        status: str,
        category: str,
    ) -> ReportFilters:
        return ReportFilters(
            date_from=date(date_from.year(), date_from.month(), date_from.day()),
            date_to=date(date_to.year(), date_to.month(), date_to.day()),
            customer_id=customer_id,
            supplier_id=supplier_id,
            salesperson=salesperson or "all",
            status=status or "all",
            category=category or "all",
        )
