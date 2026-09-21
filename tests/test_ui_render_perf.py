"""UI render/startup performance regressions (no business-logic changes)."""

from __future__ import annotations

import time

from PySide6.QtWidgets import QGraphicsDropShadowEffect

from app.core.lazy_page import LazyPage
from app.theme.theme import theme_manager
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.toolbar.modern_toolbar import ModernToolbar
from app.windows.dashboard import Dashboard
from app.windows.main_window import MainWindow


def test_enterprise_card_has_no_graphics_shadow(qt_app):
    card = EnterpriseCard("DashboardCard")
    assert card.graphicsEffect() is None
    assert not isinstance(card.graphicsEffect(), QGraphicsDropShadowEffect)


def test_toolbar_has_no_graphics_shadow(qt_app):
    bar = ModernToolbar()
    assert bar.graphicsEffect() is None


def test_toolbar_search_wired(qt_app):
    """ToolbarSearch is mounted and exposed for Ctrl+F / page filter forwarding."""
    bar = ModernToolbar()
    bar.show()
    bar.resize(1100, 52)
    qt_app.processEvents()
    assert bar.search is not None
    assert bar.search.objectName() == "ToolbarSearch"
    assert bar.search.isVisible()
    bar.search.setText("probe")
    assert bar.search.text() == "probe"
    bar.set_context(1)
    assert bar.search.text() == ""
    bar.close()


def test_dashboard_kpi_hierarchy(qt_app):
    """Primary Promet KPI is dominant; warning/danger tones preserved."""
    dash = Dashboard()
    assert dash._kpi_revenue.property("tone") == "primary"
    assert dash._kpi_revenue.property("prominence") == "dominant"
    assert dash._kpi_unpaid.property("tone") == "warning"
    assert dash._kpi_overdue.property("tone") == "danger"
    assert dash._kpi_invoices.property("tone") == "neutral"
    assert dash._kpi_revenue.minimumHeight() > dash._kpi_unpaid.minimumHeight()
    dash._place_widgets(1400)
    assert dash._breakpoint == "wide"
    # Hero revenue occupies two columns in the wide KPI row.
    pos = dash._grid.getItemPosition(dash._grid.indexOf(dash._kpi_revenue))
    assert pos[2] == 1  # row span
    assert pos[3] == 2  # column span


def test_dashboard_defers_data_until_show(qt_app):
    dash = Dashboard()
    assert dash._data_loaded is False
    dash.show()
    qt_app.processEvents()
    assert dash._data_loaded is True


def test_theme_qss_template_cached(qt_app):
    first = theme_manager.load_qss_template()
    second = theme_manager.load_qss_template()
    assert first is second
    built_a = theme_manager.build_stylesheet()
    built_b = theme_manager.build_stylesheet()
    assert built_a is built_b


def test_lazy_pages_not_built_at_startup(qt_app):
    window = MainWindow()
    assert isinstance(window.invoices, LazyPage)
    assert window.invoices.is_loaded is False
    assert window.settings.is_loaded is False
    window.close()


def test_mainwindow_construct_budget(qt_app):
    """Shell construction must stay fast; dashboard DB fill is deferred."""
    started = time.perf_counter()
    window = MainWindow()
    construct_ms = (time.perf_counter() - started) * 1000
    assert window.dashboard._data_loaded is False
    window.show()
    qt_app.processEvents()
    # Allow deferred refresh tick.
    qt_app.processEvents()
    shown_ms = (time.perf_counter() - started) * 1000
    window.close()
    # Construction alone should be well under a couple seconds on CI hardware.
    assert construct_ms < 2500, f"MainWindow construct too slow: {construct_ms:.0f}ms"
    assert shown_ms < 4000, f"MainWindow show path too slow: {shown_ms:.0f}ms"


def test_navigation_switch_budget(qt_app):
    """Stack switch itself must stay snappy; heavy refresh is deferred."""
    window = MainWindow()
    window.show()
    qt_app.processEvents()
    qt_app.processEvents()

    started = time.perf_counter()
    window.change_page(2)  # customers — first visit builds page synchronously
    switch_ms = (time.perf_counter() - started) * 1000
    qt_app.processEvents()
    window.close()
    # First visit includes page construct; keep under a generous CI budget.
    assert switch_ms < 5000, f"Page switch too slow: {switch_ms:.0f}ms"
