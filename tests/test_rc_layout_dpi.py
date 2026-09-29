"""RC fixes: layouts at 100-150 % scaling (Settings, toolbar, invoice list), themed indicators."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.core.permissions import set_identity
from app.core.session import session
from app.core.ui.layouts import detach_widgets
from app.modules.settings.settings_page import SettingsPage
from app.theme.colors import PALETTES, ThemeMode
from app.theme.indicators import ICON_DIR, indicator_tokens
from app.theme.theme import ThemeManager
from app.theme.tokens import CONTROL_HEIGHT
from app.widgets.settings.settings_health_card import SettingsHealthCard
from app.widgets.settings.settings_nav import SettingsNav
from app.widgets.toolbar.modern_toolbar import ModernToolbar

ROOT = Path(__file__).resolve().parent.parent
MODES = (ThemeMode.LIGHT, ThemeMode.DARK)


def _pump(app, n: int = 30) -> None:
    for _ in range(n):
        app.processEvents()


def _near(color: QColor, ref: QColor, tol: int = 40) -> bool:
    return max(abs(color.red() - ref.red()), abs(color.green() - ref.green()),
               abs(color.blue() - ref.blue())) <= tol


def _themed_host(mode: ThemeMode) -> QWidget:
    host = QWidget()
    host.setStyleSheet(ThemeManager().build_stylesheet(mode))
    return host


# ------------------------------------------------------------ responsive re-layout


def test_detach_widgets_keeps_the_readded_widget_height_for_width_live(qt_app):
    canvas = QWidget()
    grid = QGridLayout(canvas)
    card = QWidget()
    label = QLabel("kratko")
    label.setWordWrap(True)
    QVBoxLayout(card).addWidget(label)
    grid.addWidget(card, 0, 0)
    canvas.resize(200, 400)
    canvas.show()
    _pump(qt_app)

    detach_widgets(grid)
    assert grid.count() == 0
    assert not card.isHidden()
    grid.addWidget(card, 0, 0)
    _pump(qt_app)
    label.setText("besedilo, ki se mora prelomiti v več vrstic " * 4)
    _pump(qt_app)
    assert grid.itemAt(0).heightForWidth(200) == card.heightForWidth(200)
    canvas.close()


def test_health_tiles_choose_columns_from_the_available_width(qt_app):
    card = SettingsHealthCard()
    widths = [tile.minimumSizeHint().width() for tile in card._cards]
    spacing = card._tiles.horizontalSpacing()
    card.fit_columns(sum(widths) + 3 * spacing)
    assert card._columns == 4
    card.fit_columns(sum(widths) + 3 * spacing - 1)
    assert card._columns == 2
    card.fit_columns(max(widths))
    assert card._columns == 1
    card.close()


def _settings_window(qt_app, *sizes):
    session.login("Administrator", "Administrator")
    session.locked = False
    window = QMainWindow()
    page = SettingsPage()
    window.setCentralWidget(page)
    window.resize(*sizes[0])
    window.show()
    _pump(qt_app)
    if not page._data_loaded:
        page.refresh()
    _pump(qt_app, 60)
    for size in sizes[1:]:
        window.resize(*size)
        _pump(qt_app, 60)
    return window, page


def test_settings_health_tiles_fit_their_card_after_breakpoint_changes(qt_app):
    for sizes in (
        [(1300, 900)],
        [(1100, 900)],
        [(900, 900)],
        [(700, 820), (1224, 820)],
        [(1700, 900), (1100, 900)],
    ):
        window, page = _settings_window(qt_app, *sizes)
        card = page.health_card
        rects = [tile.geometry() for tile in card._cards]
        overlaps = [(i, j) for i in range(4) for j in range(i + 1, 4) if rects[i].intersects(rects[j])]
        assert overlaps == [], sizes
        # Neither squeezed (tiles overlap) nor left at an old, taller height (a gap).
        needed = card.heightForWidth(card.width())
        assert abs(card.height() - needed) <= 4, (sizes, card.height(), needed)
        window.close()


def test_settings_nav_follows_the_width_inside_the_narrow_layout(qt_app):
    window, page = _settings_window(qt_app, (700, 820))
    assert page._breakpoint == "narrow"
    assert not page.nav.isVisible()
    window.resize(1224, 820)
    _pump(qt_app, 60)
    assert page._breakpoint == "narrow"
    assert page.nav.isVisible()
    window.close()


def test_settings_nav_scrolls_so_every_category_stays_reachable(qt_app):
    nav = SettingsNav()
    assert nav.minimumSizeHint().height() < 300
    nav.resize(nav.width(), 380)
    nav.show()
    _pump(qt_app)
    viewport = nav._scroll.viewport()
    assert nav._scroll.verticalScrollBar().maximum() > 0
    for key, button in nav._buttons.items():
        nav.select(key)
        _pump(qt_app, 5)
        top = button.mapTo(viewport, QPoint(0, 0)).y()
        assert top >= 0 and top + button.height() <= viewport.height(), key
    nav.close()


def test_settings_nav_list_shows_the_rail_surface_in_both_themes(qt_app):
    for mode in MODES:
        host = _themed_host(mode)
        nav = SettingsNav()
        QVBoxLayout(host).addWidget(nav)
        host.resize(260, 900)
        host.show()
        _pump(qt_app)
        viewport = nav._scroll.viewport()
        last = nav._buttons["danger"]
        y = last.mapTo(nav, QPoint(0, last.height())).y() + 20
        assert y < viewport.mapTo(nav, QPoint(0, viewport.height())).y()
        pixel = QColor(nav.grab().toImage().pixel(nav.width() // 2, y))
        assert pixel.name() == QColor(PALETTES[mode]["SURFACE"]).name(), mode
        host.close()


def test_toolbar_controls_are_control_height_and_inside_the_bar(qt_app):
    set_identity(role="Administrator", authenticated=True)
    for mode in MODES:
        host = _themed_host(mode)
        bar = ModernToolbar()
        QVBoxLayout(host).addWidget(bar)
        host.resize(1300, 80)
        host.show()
        _pump(qt_app)
        inside = bar.contentsRect()
        controls = (bar.search, bar.actions.btn_new, bar.actions.btn_lock,
                    bar.actions.btn_settings, bar.user.button)
        for control in (c for c in controls if c.isVisible()):
            name = control.objectName() or control.text()
            assert control.height() == CONTROL_HEIGHT, (mode, name, control.height())
            # Children are clipped to their parent, so every host must hold the whole control.
            assert control.parentWidget().rect().contains(control.geometry()), (mode, name)
            top_left = control.mapTo(bar, QPoint(0, 0))
            assert inside.contains(control.rect().translated(top_left)), (mode, name)
        host.close()


def test_invoice_list_customer_column_keeps_stretching_after_reload(qt_app):
    from app.modules.invoices.invoice_page import InvoicePage

    set_identity(role="Administrator", authenticated=True)
    page = InvoicePage()
    page.resize(1200, 700)
    page.show()
    _pump(qt_app)
    page.model.refresh([(1, "2026-001", "29.09.2026", "Stranka d.o.o.", 41.0, "Osnutek")])
    _pump(qt_app)
    header = page.table.horizontalHeader()
    assert header.sectionResizeMode(3) == QHeaderView.Stretch
    visible = [c for c in range(page.model.columnCount()) if not page.table.isColumnHidden(c)]
    assert sum(header.sectionSize(c) for c in visible) >= page.table.viewport().width() - 2
    page.close()


_ARTICLES_TOOLBAR_PROBE = r"""
import json
import sys

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QFontInfo
from PySide6.QtWidgets import QApplication, QLayout, QPushButton, QVBoxLayout, QWidget

app = QApplication([])

from app.core.permissions import set_identity
from app.database.database import db
from app.modules.articles.article_page import ArticlePage
from app.theme.colors import ThemeMode
from app.theme.theme import ThemeManager

db.initialize()
set_identity(role="Administrator", authenticated=True)
width = int(sys.argv[1])
report = {}
for mode in (ThemeMode.LIGHT, ThemeMode.DARK):
    host = QWidget()
    host.setStyleSheet(ThemeManager().build_stylesheet(mode))
    row = QVBoxLayout(host)
    row.setContentsMargins(0, 0, 0, 0)
    # Like the main window's page stack, the host does not grow to the page's minimum width.
    row.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
    page = ArticlePage()
    row.addWidget(page)
    host.resize(width, 600)
    host.show()
    app.processEvents()
    toolbar = page.actions.parentWidget()
    host.resize(host.width() + width - toolbar.width(), 600)
    for _ in range(30):
        app.processEvents()
    controls = [page.search_field, page.actions.filter] + [
        b for b in page.actions.findChildren(QPushButton) if b.isVisible()
    ]
    rects = [(c.objectName() or c.text(), QRect(c.mapTo(toolbar, QPoint(0, 0)), c.size())) for c in controls]
    report[mode.value] = {
        "font": QFontInfo(page.actions.btn_edit.font()).family(),
        "toolbar_width": toolbar.width(),
        "outside": [name for name, rect in rects if not toolbar.rect().contains(rect)],
        "overlaps": [[a, b] for i, (a, ra) in enumerate(rects) for b, rb in rects[i + 1:] if ra.intersects(rb)],
    }
    host.close()
print(json.dumps(report))
"""


def _run_layout_probe(tmp_path: Path, script: str, *args: str,
                      screen: tuple[int, int] | None = None) -> dict:
    """Run ``script`` in a child Qt process that has the Windows fonts; return its JSON output.

    pytest's offscreen platform falls back to a much wider generic font, so pixel budgets are
    measured where Segoe UI loads (the same metrics as the real platform). ``screen`` is the
    logical available screen size; data paths point into ``tmp_path``.
    """
    import json
    import os
    import subprocess
    import sys

    import pytest

    fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if not (fonts / "segoeui.ttf").is_file():
        pytest.skip("needs Segoe UI, the font the product is laid out with")
    tmp_path.mkdir(parents=True, exist_ok=True)
    platform = "offscreen"
    if screen is not None:
        config = tmp_path / "screen.json"
        config.write_text(json.dumps({"screens": [{
            "name": "probe", "x": 0, "y": 0, "width": screen[0], "height": screen[1],
            "logicalDpi": 96, "logicalBaseDpi": 96, "dpr": 1,
        }]}))
        # The platform argument is split on ':', so the path must not carry a drive letter.
        platform += ":configfile=" + os.path.relpath(config, ROOT).replace("\\", "/")
    env = dict(os.environ, QT_QPA_PLATFORM=platform, QT_QPA_FONTDIR=str(fonts))
    for key, sub in (("JU_TAN_DATA_DIR", "data"), ("JU_TAN_EXPORT_DIR", "exports"),
                     ("JU_TAN_REPORT_DIR", "reports"), ("JU_TAN_BACKUP_DIR", "backups"),
                     ("JU_TAN_LOG_DIR", "logs"), ("LOCALAPPDATA", "localappdata")):
        env[key] = str(tmp_path / sub)
    env["JU_TAN_DATABASE"] = str(tmp_path / "data" / "probe.db")
    probe = subprocess.run(
        [sys.executable, "-c", script, *args],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert probe.returncode == 0, probe.stderr[-2000:]
    return json.loads(probe.stdout.strip().splitlines()[-1])


def test_articles_toolbar_controls_do_not_overlap_at_150_percent(tmp_path):
    # Toolbar width of the default window at 150 % on a 1920x1080 display.
    width = 884
    report = _run_layout_probe(tmp_path, _ARTICLES_TOOLBAR_PROBE, str(width))
    assert set(report) == {"light", "dark"}, report
    for mode, result in report.items():
        assert result["font"] == "Segoe UI", (mode, result)
        assert result["toolbar_width"] == width, (mode, result)
        assert result["outside"] == [], (mode, result)
        assert result["overlaps"] == [], (mode, result)


def _compressed_labels(root: QWidget) -> list[tuple[str, int, int]]:
    """Visible text labels shorter than their text needs at their current width."""
    found = []
    for label in root.findChildren(QLabel):
        if not label.isVisible() or not label.text().strip():
            continue
        need = label.heightForWidth(label.width()) if label.wordWrap() else label.minimumSizeHint().height()
        if label.height() < need - 1:
            found.append((label.text()[:40], label.height(), need))
    return found


def _unconstrained_host(widget: QWidget) -> QWidget:
    """Themed host that, like the main window's page stack, does not grow to the widget's minimum."""
    from PySide6.QtWidgets import QLayout

    host = _themed_host(ThemeMode.LIGHT)
    row = QVBoxLayout(host)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
    row.addWidget(widget)
    return host


_WIZARD_PROBE = r"""
import json

from PySide6.QtGui import QFontInfo
from PySide6.QtWidgets import QApplication, QLabel

app = QApplication([])

from app.database.database import db
from app.theme.colors import ThemeMode
from app.theme.theme import ThemeManager
from app.windows.first_run_wizard import FirstRunWizard

db.initialize()
app.setStyleSheet(ThemeManager().build_stylesheet(ThemeMode.DARK))
wizard = FirstRunWizard()
wizard.show()
for _ in range(50):
    app.processEvents()
column = next(label for label in wizard.findChildren(QLabel)
              if label.objectName() == "FirstRunLead" and label.text().startswith("Dobrodošli")).parentWidget()
report = {"font": QFontInfo(wizard.btn_next.font()).family(), "steps": {},
          "welcome_column": [column.height(), column.sizeHint().height()]}
for step in range(wizard.stack.count()):
    wizard._show_step(step)
    for _ in range(30):
        app.processEvents()
    compressed = []
    for label in wizard.stack.currentWidget().findChildren(QLabel):
        if not label.isVisible() or not label.text().strip():
            continue
        need = label.heightForWidth(label.width()) if label.wordWrap() else label.minimumSizeHint().height()
        if label.height() < need - 1:
            compressed.append([label.text()[:40], label.height(), need])
    report["steps"][step] = compressed
wizard.close()
print(json.dumps(report))
"""


def test_first_run_wizard_steps_give_wrapped_text_its_full_height(tmp_path):
    # Logical available screen of a 1920x1080 display at 125 % and at 150 %.
    for screen in ((1536, 816), (1280, 680)):
        report = _run_layout_probe(tmp_path / f"{screen[1]}", _WIZARD_PROBE, screen=screen)
        assert report["font"] == "Segoe UI", (screen, report)
        assert report["steps"] == {str(step): [] for step in range(6)}, (screen, report)
        # Windows wraps the lead into one line more than the probe's font engine, so even a few
        # pixels less than the column's preferred height clip text on the real platform.
        height, preferred = report["welcome_column"]
        assert height >= preferred, (screen, report)


def test_details_panels_scroll_instead_of_collapsing_their_rows(qt_app):
    from PySide6.QtWidgets import QScrollArea

    from app.modules.customers.customer_details import CustomerDetails
    from app.modules.offers.offer_details import OfferDetails
    from app.modules.orders.order_details import OrderDetails
    from app.modules.payments.payment_details import PaymentDetails

    for panel in (CustomerDetails, PaymentDetails, OfferDetails, OrderDetails):
        details = panel()
        host = _unconstrained_host(details)
        host.resize(300, 200)
        host.show()
        _pump(qt_app)
        assert _compressed_labels(details) == [], panel.__name__
        scroll = details.findChild(QScrollArea)
        assert scroll is not None and scroll.verticalScrollBar().maximum() > 0, panel.__name__
        # The page splitter honours the minimum width, so it must still cover the card.
        assert details.minimumSizeHint().width() >= scroll.widget().minimumSizeHint().width(), panel.__name__
        host.close()


def test_customer_tax_field_shows_a_whole_vat_id_at_its_minimum_width(qt_app):
    from PySide6.QtWidgets import QStyle, QStyleOptionFrame

    from app.widgets.customers.customer_form import CustomerForm

    form = CustomerForm()
    host = _themed_host(ThemeMode.LIGHT)
    QVBoxLayout(host).addWidget(form)
    host.show()
    _pump(qt_app)
    host.resize(host.minimumSizeHint())
    _pump(qt_app)
    field = form.tax_number
    option = QStyleOptionFrame()
    field.initStyleOption(option)
    contents = field.style().subElementRect(QStyle.SE_LineEditContents, option, field)
    margins = field.textMargins()
    usable = contents.width() - margins.left() - margins.right() - 2 * 2
    for vat_id in ("SI12345678", "HR12345678901"):
        assert field.fontMetrics().horizontalAdvance(vat_id) <= usable, (vat_id, usable)
    host.close()


def test_payments_table_stays_inside_its_card_when_the_splitter_is_short(qt_app):
    from app.modules.payments.payment_page import PaymentPage

    set_identity(role="Administrator", authenticated=True)
    page = PaymentPage()
    host = _unconstrained_host(page)
    host.resize(1000, 700)
    host.show()
    page.content_stack.setCurrentIndex(1)
    _pump(qt_app)
    # Splitter height below the KPI row in the default window at 150 % (1152 x 578).
    target = 220
    stack = page.content_stack
    for _ in range(3):
        host.resize(1000, host.height() + target - stack.height())
        _pump(qt_app)
    assert abs(stack.height() - target) <= 2, stack.height()
    card = page.table.parentWidget()
    assert card.rect().contains(page.table.geometry()), (card.size(), page.table.geometry())
    assert _compressed_labels(page.details) == []
    host.close()


# ------------------------------------------------------------ card surfaces


def _surface_leaks(root: QWidget) -> list[tuple[str, str, str]]:
    """Plain QWidget containers without an ID rule that paint a colour other than the surface behind.

    Only an exact QWidget paints the global ``QWidget { background }`` rule; without a rule of
    its own, a difference is the window background showing through as a patch.
    """
    import re

    image = root.grab().toImage()
    dpr = image.devicePixelRatio()
    styled = set(re.findall(r"#([A-Za-z_]\w*)", root.styleSheet()))

    def free_point(w: QWidget) -> QPoint | None:
        # Off straight edges and out of the corners: borders and rounded corners are not surface.
        cover = [c.geometry().adjusted(-1, -1, 1, 1) for c in w.children()
                 if isinstance(c, QWidget) and c.isVisible() and not c.isWindow()]
        for y in range(4, w.height() - 4, 2):
            edge = 4 if 24 <= y < w.height() - 24 else 24
            x = edge
            for left, right in sorted((r.left(), r.right()) for r in cover if r.top() <= y <= r.bottom()):
                if left > x:
                    break
                x = max(x, right + 1)
            if x < w.width() - edge:
                return w.mapTo(root, QPoint(x, y))
        return None

    leaks = []
    for w in root.findChildren(QWidget):
        parent = w.parentWidget()
        # qt_* are Qt's own parts, e.g. a text edit's viewport, which paints the text itself.
        if (type(w) is not QWidget or w.objectName() in styled or w.objectName().startswith("qt_")
                or not w.isVisible() or parent is None or not w.testAttribute(Qt.WA_StyledBackground)):
            continue
        own, behind = free_point(w), free_point(parent)
        if own is None or behind is None:
            continue
        a = QColor(image.pixel(int(own.x() * dpr), int(own.y() * dpr)))
        b = QColor(image.pixel(int(behind.x() * dpr), int(behind.y() * dpr)))
        if not _near(a, b, tol=4):
            leaks.append((parent.objectName() or type(parent).__name__, a.name(), b.name()))
    return leaks


def test_layout_containers_do_not_paint_patches_on_card_surfaces(qt_app, monkeypatch):
    import app.widgets.settings.license_card as license_card_mod
    from app.widgets.cards.enterprise_card import EnterpriseCard
    from app.widgets.customers.customer_form import CustomerForm
    from app.widgets.dashboard.quick_actions import QuickActionsCard
    from app.widgets.settings.about_card import AboutCard
    from app.widgets.settings.license_card import LicenseCard

    monkeypatch.setattr(license_card_mod.LicenseState, "load", classmethod(lambda cls: None))
    monkeypatch.setattr(license_card_mod, "_plan_label", lambda: "")
    monkeypatch.setattr(license_card_mod, "_expiry_label", lambda: "")

    def customer_form_on_card():
        card = EnterpriseCard("DashboardCard")
        card.body.addWidget(CustomerForm())
        return card

    components = {"quick actions": QuickActionsCard, "license": LicenseCard, "about": AboutCard,
                  "customer form": customer_form_on_card}
    for mode in MODES:
        for name, factory in components.items():
            host = _themed_host(mode)
            QVBoxLayout(host).addWidget(factory())
            host.resize(900, 700)
            host.show()
            _pump(qt_app)
            assert _surface_leaks(host) == [], (mode, name)
            host.close()


def test_first_run_welcome_sits_on_the_card_surface(qt_app):
    from app.windows.first_run_wizard import FirstRunWizard

    for mode in MODES:
        wizard = FirstRunWizard()
        wizard.setStyleSheet(ThemeManager().build_stylesheet(mode))
        wizard.show()
        _pump(qt_app)
        assert _surface_leaks(wizard) == [], mode
        wizard.done(0)


# ------------------------------------------------------------ themed indicators


def test_dropdown_arrow_is_a_chevron_not_a_filled_block(qt_app):
    for mode in MODES:
        host = _themed_host(mode)
        combo = QComboBox(host)
        combo.addItems(["kos", "ura"])
        combo.setFixedSize(180, 38)
        host.show()
        _pump(qt_app)
        image = combo.grab().toImage()
        arrow = QColor(PALETTES[mode]["TEXT_MUTED"])
        points = [(x, y) for x in range(image.width() - 28, image.width() - 2)
                  for y in range(4, image.height() - 4) if _near(QColor(image.pixel(x, y)), arrow, 48)]
        assert len(points) >= 8, mode
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        box = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
        assert len(points) / box < 0.6, (mode, len(points), box)
        host.close()


def test_checkbox_and_radio_indicators_are_visible_in_both_themes(qt_app):
    for mode in MODES:
        palette = PALETTES[mode]
        host = _themed_host(mode)
        row = QHBoxLayout(host)
        widgets = (QCheckBox("Možnost"), QRadioButton("Izbira"))
        for widget in widgets:
            # The resting look; a focused indicator is drawn with a PRIMARY border.
            widget.setFocusPolicy(Qt.NoFocus)
            row.addWidget(widget)
        host.show()
        _pump(qt_app)
        for widget in widgets:
            for checked in (False, True):
                widget.setChecked(checked)
                _pump(qt_app, 5)
                image = widget.grab().toImage()
                area = [(x, y, QColor(image.pixel(x, y))) for x in range(min(22, image.width()))
                        for y in range(image.height())]
                ref = QColor(palette["PRIMARY"] if checked else palette["TEXT_MUTED"])
                hits = [(x, y) for x, y, c in area if _near(c, ref, 30)]
                assert len(hits) >= 12, (mode, type(widget).__name__, checked)
                if checked:
                    x0, x1 = min(x for x, _ in hits), max(x for x, _ in hits)
                    y0, y1 = min(y for _, y in hits), max(y for _, y in hits)
                    mark = [c for x, y, c in area if x0 < x < x1 and y0 < y < y1 and c.lightness() > 230]
                    assert len(mark) >= 3, (mode, type(widget).__name__)
        host.close()


def _contrast(a: str, b: str) -> float:
    def luminance(value: str) -> float:
        colour = QColor(value)
        channels = []
        for v in (colour.red(), colour.green(), colour.blue()):
            v /= 255
            channels.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_danger_button_icon_and_label_stay_visible_on_hover(qt_app):
    from collections import Counter

    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QPushButton

    from app.core.ui.icons import apply_button_icon
    from app.theme.theme import theme_manager

    previous = theme_manager.mode
    try:
        for mode in MODES:
            palette = PALETTES[mode]
            for fill in ("DANGER_SOFT", "DANGER_SOFT_PRESSED"):
                assert _contrast(palette["DANGER"], palette[fill]) >= 3.0, (mode, fill)  # icon
                assert _contrast(palette["DANGER_ON_SOFT"], palette[fill]) >= 4.5, (mode, fill)  # label
            # The icon colour comes from the active theme, so apply it app-wide.
            theme_manager.apply(qt_app, mode, force=True)
            host = QWidget()
            row = QHBoxLayout(host)
            button = QPushButton("Odstrani")
            button.setObjectName("DangerButton")
            button.setFocusPolicy(Qt.NoFocus)
            apply_button_icon(button, "delete")
            row.addWidget(button)
            host.show()
            _pump(qt_app)
            # Leave first: a move to the previous cursor position sends no enter event.
            QTest.mouseMove(host, QPoint(1, 1))
            QTest.mouseMove(button, button.rect().center())
            _pump(qt_app, 10)
            image = button.grab().toImage()
            inner = [QColor(image.pixel(x, y)) for x in range(3, image.width() - 3)
                     for y in range(3, image.height() - 3)]
            fill = Counter(c.name() for c in inner).most_common(1)[0][0]
            assert fill == palette["DANGER_SOFT"].lower(), (mode, fill)
            # Inside the border, DANGER pixels are the icon's; they must not blend into the fill.
            icon = [c for c in inner if _near(c, QColor(palette["DANGER"]), 30)]
            assert len(icon) >= 8, (mode, len(icon))
            host.close()
    finally:
        theme_manager.apply(qt_app, previous, force=True)


def test_indicator_svgs_use_the_palette_colours():
    for mode, theme in ((ThemeMode.LIGHT, "light"), (ThemeMode.DARK, "dark")):
        palette = PALETTES[mode]
        for name, token in (("chevron-down", "TEXT_MUTED"), ("chevron-up", "TEXT_MUTED"),
                            ("chevron-down-disabled", "DISABLED"), ("chevron-up-disabled", "DISABLED")):
            svg = (ICON_DIR / f"{name}-{theme}.svg").read_text(encoding="utf-8").lower()
            assert f'stroke="{palette[token].lower()}"' in svg, (name, theme)
        # The check mark and radio dot sit on PRIMARY.
        assert palette["ON_PRIMARY"].lower() == "#ffffff"
    assert 'stroke="#ffffff"' in (ICON_DIR / "check.svg").read_text(encoding="utf-8").lower()
    assert 'fill="#ffffff"' in (ICON_DIR / "radio-dot.svg").read_text(encoding="utf-8").lower()


def test_indicator_tokens_are_quoted_forward_slash_paths_to_existing_files():
    for mode in MODES:
        for key, value in indicator_tokens(mode).items():
            assert value.startswith('"') and value.endswith('"'), key
            path = value[1:-1]
            assert "\\" not in path, key
            assert Path(path).is_file(), (key, path)
        assert "{{" not in ThemeManager().build_stylesheet(mode)


def test_release_spec_bundles_the_indicator_icons():
    spec = (ROOT / "packaging" / "ju-tan-office.spec").read_text(encoding="utf-8")
    assert '"theme" / "icons"' in spec
    assert '"app/theme/icons"' in spec
