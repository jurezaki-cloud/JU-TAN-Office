"""RC fixes: editor items table sizing, themed arrows / spin buttons, Slovenian Qt texts."""

from PySide6.QtCore import QCoreApplication, QDate, Qt
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QTableView,
    QWidget,
)

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.qt_translations import install_qt_translations
from app.core.ui.sizes import TABLE_MAX_HEIGHT, apply_dialog_table
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.modules.invoices.models.invoice_items_model import InvoiceItemsModel
from app.modules.invoices.models.invoice_table_model import InvoiceTableModel
from app.theme.colors import PALETTES, ThemeMode
from app.theme.theme import ThemeManager
from app.widgets.invoices.invoice_table import InvoiceTable

QWIDGETSIZE_MAX = 16777215


# ------------------------------------------------------------ editor items table


def test_editor_items_table_fills_panel_and_keeps_its_columns(qt_app):
    dialog = InvoiceDialog()
    dialog.show()
    qt_app.processEvents()
    dialog.fit_to_content()
    table = dialog.items_table
    apply_dialog_table(table)  # a generic dialog pass must not clamp it either
    assert table.maximumHeight() == QWIDGETSIZE_MAX
    header = table.horizontalHeader()
    assert header.sectionResizeMode(1) == QHeaderView.Stretch
    for col in (0, 2, 3, 4, 5, 7):
        assert header.sectionResizeMode(col) == QHeaderView.Interactive
    dialog.close()


def test_new_document_reserves_width_for_the_items_columns(qt_app):
    dialog = InvoiceDialog()
    panel = dialog.items_panel
    assert panel.content_stack.currentWidget() is panel.empty_state
    needed = sum(InvoiceTable.COLUMN_WIDTHS.values())
    assert panel.content_stack.sizeHint().width() >= needed
    dialog.close()


def test_invoice_table_hint_only_grows_for_the_items_layout(qt_app):
    items = InvoiceTable()
    items.setModel(InvoiceItemsModel())
    assert items.sizeHint().width() >= sum(InvoiceTable.COLUMN_WIDTHS.values())

    listing = InvoiceTable()
    listing.setModel(InvoiceTableModel())
    assert listing.sizeHint().width() == QTableView.sizeHint(listing).width()


def test_generic_dialog_tables_are_still_content_sized(qt_app):
    dialog = EnterpriseDialog(title="QA", size="SMALL")
    table = QTableView()
    dialog.body.addWidget(table)
    dialog.bind_table(table)
    assert table.maximumHeight() <= TABLE_MAX_HEIGHT
    dialog.close()


def test_dialog_scroll_area_is_not_a_tab_stop(qt_app):
    dialog = EnterpriseDialog(title="QA", size="SMALL")
    assert dialog.scroll.focusPolicy() == Qt.NoFocus
    dialog.close()


# ------------------------------------------------------------ themed sub-controls


def _host(mode: ThemeMode):
    host = QWidget()
    host.setStyleSheet(ThemeManager().build_stylesheet(mode))
    row = QHBoxLayout(host)
    combo = QComboBox()
    combo.addItems(["kos", "ura"])
    editable = QComboBox()
    editable.setEditable(True)
    editable.addItems(["22", "9.5"])
    date = QDateEdit(QDate(2026, 9, 29))
    date.setCalendarPopup(True)
    spin = QDoubleSpinBox()
    spin.setRange(0, 1000)
    spin.setValue(10)
    for widget in (combo, editable, date, spin):
        widget.setFixedSize(180, 38)
        row.addWidget(widget)
    host.show()
    return host, (combo, editable, date, spin)


def _pixels(widget, rect_fn):
    image = widget.grab().toImage()
    x0, y0, x1, y1 = rect_fn(image.width(), image.height())
    return [QColor(image.pixel(x, y)) for x in range(x0, x1) for y in range(y0, y1)]


def _near(color: QColor, ref: QColor, tol: int = 40) -> bool:
    return max(abs(color.red() - ref.red()), abs(color.green() - ref.green()),
               abs(color.blue() - ref.blue())) <= tol


def test_dropdown_and_spin_arrows_are_drawn_in_both_themes(qt_app):
    for mode in (ThemeMode.LIGHT, ThemeMode.DARK):
        arrow = QColor(PALETTES[mode]["TEXT_MUTED"])
        host, (combo, editable, date, spin) = _host(mode)
        qt_app.processEvents()
        for widget in (combo, editable, date):
            drop = _pixels(widget, lambda w, h: (w - 28, 4, w - 2, h - 4))
            assert sum(_near(c, arrow) for c in drop) >= 8, (mode, type(widget).__name__)
        up = _pixels(spin, lambda w, h: (w - 22, 2, w - 2, h // 2))
        down = _pixels(spin, lambda w, h: (w - 22, h // 2, w - 2, h - 2))
        assert sum(_near(c, arrow) for c in up) >= 6, mode
        assert sum(_near(c, arrow) for c in down) >= 6, mode
        host.close()


def test_spin_buttons_have_no_native_bevel_in_light_theme(qt_app):
    host, (_combo, _editable, date, spin) = _host(ThemeMode.LIGHT)
    qt_app.processEvents()
    for widget in (date, spin):
        area = _pixels(widget, lambda w, h: (w - 28, 1, w - 1, h - 1))
        assert not [c for c in area if c.lightness() < 60], type(widget).__name__
    host.close()


# ------------------------------------------------------------ Slovenian Qt texts


def _with_translator(qt_app):
    install_qt_translations(qt_app)
    return qt_app._jutan_qt_translator


def _drop_translator(qt_app, translator):
    qt_app.removeTranslator(translator)
    del qt_app._jutan_qt_translator


def test_standard_buttons_are_slovenian(qt_app):
    translator = _with_translator(qt_app)
    try:
        box = QMessageBox()
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        assert box.button(QMessageBox.Yes).text() == "&Da"
        assert box.button(QMessageBox.No).text() == "&Ne"
        assert box.button(QMessageBox.Cancel).text() == "Prekliči"
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        assert buttons.button(QDialogButtonBox.Ok).text() == "V redu"
        assert buttons.button(QDialogButtonBox.Cancel).text() == "Prekliči"
    finally:
        _drop_translator(qt_app, translator)


def test_unknown_strings_fall_through_unchanged(qt_app):
    translator = _with_translator(qt_app)
    try:
        assert QCoreApplication.translate("QShortcut", "Ctrl") == "Ctrl"
        assert QCoreApplication.translate("QPlatformTheme", "Not a Qt string") == "Not a Qt string"
        assert QKeySequence("Ctrl+S").toString(QKeySequence.NativeText) == "Ctrl+S"
    finally:
        _drop_translator(qt_app, translator)


def test_text_context_menu_is_slovenian_and_install_is_idempotent(qt_app):
    translator = _with_translator(qt_app)
    try:
        install_qt_translations(qt_app)
        assert qt_app._jutan_qt_translator is translator
        edit = QLineEdit()
        menu = edit.createStandardContextMenu()
        labels = [action.text().split("\t")[0] for action in menu.actions() if action.text()]
        assert "&Kopiraj" in labels and "&Prilepi" in labels and "Izberi vse" in labels
    finally:
        _drop_translator(qt_app, translator)
