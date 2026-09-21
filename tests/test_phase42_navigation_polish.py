"""Phase 4.2 — navigation & workflow polish (UI only)."""

from __future__ import annotations

from PySide6.QtCore import Qt

from app.core.session import session
from app.modules.customers.customer_page import CustomerPage
from app.modules.invoices.invoice_page import InvoicePage
from app.modules.offers.offer_page import OfferPage
from app.modules.orders.order_page import OrderPage
from app.widgets.common import EmptyState, PageHeader
from app.widgets.navigation import ModernSidebar
from app.widgets.toolbar.toolbar_title import PAGE_CONTEXT, ToolbarTitle
from app.windows.main_window import MainWindow


def test_shell_owns_page_title_no_duplicate_header(qt_app):
    """ToolbarTitle is the H1; list pages must not re-render PageHeader titles."""
    session.login("Administrator", "Administrator")
    window = MainWindow()
    window.show()
    qt_app.processEvents()

    for index, (title, _subtitle) in PAGE_CONTEXT.items():
        window.change_page(index)
        qt_app.processEvents()
        assert window.toolbar.title_block.title.text() == title

    invoices = window.invoices.ensure()
    assert invoices.findChild(PageHeader) is None
    assert not hasattr(invoices, "header")

    window.close()


def test_page_header_hides_title_by_default(qt_app):
    header = PageHeader("Računi", "Opis vsebine")
    assert header.title.text() == "Računi"
    assert header.title.isHidden()
    assert not header.description.isHidden()
    header_show = PageHeader("Računi", "Opis", show_title=True)
    assert not header_show.title.isHidden()
    header.close()
    header_show.close()


def test_list_empty_states_use_dashboard_style(qt_app):
    for factory in (InvoicePage, OfferPage, OrderPage, CustomerPage):
        page = factory()
        empty = page.empty_state
        assert isinstance(empty, EmptyState)
        assert empty.title.objectName() == "DashboardEmptyState"
        assert empty.subtitle.objectName() == "DashboardEmptyState"
        page.close()


def test_navigation_button_states(qt_app):
    session.login("Administrator", "Administrator")
    sidebar = ModernSidebar()
    sidebar.apply_role()
    sidebar.show()
    qt_app.processEvents()
    btn = sidebar.buttons[1]
    assert btn.focusPolicy() == Qt.StrongFocus

    sidebar.set_active(1)
    assert btn.isChecked()
    assert not sidebar.buttons[0].isChecked()

    btn.setFocus(Qt.TabFocusReason)
    qt_app.processEvents()
    assert btn.hasFocus()

    btn.setEnabled(False)
    qt_app.processEvents()
    assert not btn.isEnabled()
    btn.setEnabled(True)

    sidebar.close()


def test_toolbar_title_context_covers_all_pages(qt_app):
    block = ToolbarTitle()
    for index in range(18):
        block.set_context(index)
        title, subtitle = PAGE_CONTEXT[index]
        assert block.title.text() == title
        assert block.subtitle.text() == subtitle
    block.close()
