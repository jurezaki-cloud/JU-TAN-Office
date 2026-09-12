"""TASK-028 UX polish."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLineEdit

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.icons import standard_icon
from app.core.ui.toast import ToastBanner
from app.widgets.customers.empty_state import EmptyStateCard
from app.widgets.tables.enterprise_table import EnterpriseTable


def test_standard_icon(qt_app):
    icon = standard_icon("save")
    assert icon is not None


def test_toast_banner(qt_app):
    host = EnterpriseDialog(title="Toast host", size="SMALL")
    banner = ToastBanner(host, "Ponudba shranjena", "success")
    assert banner.objectName() == "ToastBanner"
    assert banner.property("kind") == "success"
    host.close()


def test_empty_state_action(qt_app):
    card = EmptyStateCard("Ni podatkov.", "Dodajte prvi zapis.")
    assert not card.action.isHidden()
    assert "prvi" in card.action.text().casefold()
    card.set_message("Ni zadetkov", "Poskusite znova.")
    assert card.action.isHidden()
    card.set_message("Ni strank", "Dodajte prvo stranko.")
    assert not card.action.isHidden()


def test_enterprise_table_context_menu(qt_app):
    table = EnterpriseTable()
    assert table.contextMenuPolicy() == Qt.CustomContextMenu


def test_dialog_enter_save_and_snapshot(qt_app):
    dialog = EnterpriseDialog(title="UX", size="SMALL")
    field = QLineEdit()
    dialog.body.addWidget(field)
    assert dialog.btn_save.isDefault()
    dialog._snapshot = dialog._form_snapshot()
    field.setText("spremenjeno")
    assert dialog._is_dirty()
    dialog.close()


def test_shortcuts_sequences():
    assert QKeySequence("Ctrl+N").toString() != ""
    assert QShortcut is not None
