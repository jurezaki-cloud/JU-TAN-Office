"""Progress / spinner za daljša opravila."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QProgressDialog, QWidget


def run_busy(
    parent: QWidget | None,
    title: str,
    work: Callable[[], Any],
    *,
    cancellable: bool = False,
) -> Any:
    dialog = QProgressDialog(title, "Prekliči" if cancellable else "", 0, 0, parent)
    dialog.setWindowTitle("Opravilo")
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setMinimumDuration(400)
    if not cancellable:
        dialog.setCancelButton(None)
    dialog.show()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    try:
        if cancellable and dialog.wasCanceled():
            return None
        return work()
    finally:
        dialog.close()
        dialog.deleteLater()
