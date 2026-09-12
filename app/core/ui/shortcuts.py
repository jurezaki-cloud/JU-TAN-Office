"""Globalne bližnjice glavnega okna."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLineEdit, QWidget

NEW_METHODS = (
    "new_invoice",
    "new_customer",
    "new_offer",
    "new_article",
    "new_order",
    "new_payment",
    "new_supplier",
    "new_purchase",
    "new_lead",
    "new_rule",
    "new_movement",
    "new_folder",
)
SAVE_METHODS = ("save", "_save")
PRINT_METHODS = ("print_pdf", "print_stock", "print_pipeline", "print_report", "export_pdf")
EXPORT_METHODS = ("export_excel", "export_list", "export_csv")


def _page(window) -> QWidget | None:
    stack = getattr(window, "stack", None)
    if stack is None:
        return None
    widget = stack.currentWidget()
    ensure = getattr(widget, "ensure", None)
    if callable(ensure):
        return ensure()
    return widget


def _call_first(target, names: tuple[str, ...]) -> bool:
    if target is None:
        return False
    for name in names:
        method = getattr(target, name, None)
        if callable(method):
            method()
            return True
    return False


def install_shortcuts(window) -> None:
    def bind(seq: str, fn) -> None:
        shortcut = QShortcut(QKeySequence(seq), window)
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(fn)

    bind("Ctrl+N", lambda: _call_first(_page(window), NEW_METHODS) or _emit_new(window))
    bind("Ctrl+S", lambda: _call_first(_page(window), SAVE_METHODS))
    bind("Ctrl+F", lambda: _focus_search(window))
    bind("Ctrl+P", lambda: _print(window))
    bind("Ctrl+E", lambda: _export(window))
    bind("Ctrl+K", lambda: _palette(window))
    bind("F5", lambda: _call_first(_page(window), ("refresh",)))


def _emit_new(window) -> None:
    toolbar = getattr(window, "toolbar", None)
    if toolbar is not None:
        toolbar.new_invoice_clicked.emit()


def _signal_or_call(page, method_names, signal_names) -> bool:
    if _call_first(page, method_names):
        return True
    actions = getattr(page, "actions", None)
    if actions is None:
        return False
    for name in signal_names:
        signal = getattr(actions, name, None)
        if signal is not None and hasattr(signal, "emit"):
            signal.emit()
            return True
    return False


def _print(window) -> None:
    _signal_or_call(_page(window), PRINT_METHODS, ("print_clicked", "pdf_clicked"))


def _export(window) -> None:
    _signal_or_call(_page(window), EXPORT_METHODS, ("excel_clicked", "export_clicked"))


def _focus_search(window) -> None:
    page = _page(window)
    search = getattr(page, "search", None) if page is not None else None
    if search is None:
        search = getattr(getattr(window, "toolbar", None), "search", None)
    if isinstance(search, QLineEdit):
        search.setFocus()
        search.selectAll()


def _palette(window) -> None:
    from app.core.ui.command_palette import CommandPalette

    dialog = CommandPalette(window)
    if dialog.exec():
        index = dialog.chosen_index()
        if index is not None:
            window.change_page(index)
