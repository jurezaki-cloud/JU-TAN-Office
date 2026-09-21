"""Glavno okno — fiksni indeksi QStackedWidget, strani se naložijo ob prvem obisku."""

from __future__ import annotations
from PySide6.QtWidgets import QDialog

import sys

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.core.lazy_page import LazyPage
from app.core.logger import install_excepthook, logger
from app.widgets.common.responsive_stack import ResponsiveStackedWidget
from app.widgets.navigation import ModernSidebar
from app.widgets.statusbar import StatusBar
from app.widgets.toolbar import ModernToolbar
from app.windows.dashboard import Dashboard


class EmptyPage(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel(title)
        label.setObjectName("PageTitleLarge")
        label.hide()
        layout.addWidget(label)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from app.core.constants import APP_NAME
        from app.core.ui.app_identity import apply_native_titlebar_theme, apply_window_icon
        from app.theme.theme import theme_manager

        self.setWindowTitle(APP_NAME)
        apply_window_icon(self)
        self.resize(1400, 900)
        try:
            from app.core.ui.sizes import preset_size
            self.resize(preset_size("XL"))
        except Exception:
            pass
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "main_window", geometry=True)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = ModernSidebar()
        self.sidebar.apply_role()
        root_layout.addWidget(self.sidebar)

        right = QWidget()
        right.setObjectName("AppWorkspace")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        self.toolbar = ModernToolbar()
        right_layout.addWidget(self.toolbar)

        self.stack = ResponsiveStackedWidget()

        self.dashboard = Dashboard()
        self.invoices = LazyPage(_page_invoices, "Računi")
        self.customers = LazyPage(_page_customers, "Stranke")
        self.offers = LazyPage(_page_offers, "Ponudbe")
        self.articles = LazyPage(_page_articles, "Artikli")
        self.company = LazyPage(_page_company, "Podjetje")
        self.orders = LazyPage(_page_orders, "Naročila")
        self.analytics = LazyPage(_page_analytics, "Analitika")
        self.payments = LazyPage(_page_payments, "Plačila")
        self.settings = LazyPage(_page_settings, "Nastavitve")
        self.warehouse = LazyPage(_page_warehouse, "Skladišče")
        self.suppliers = LazyPage(_page_suppliers, "Dobavitelji")
        self.purchase = LazyPage(_page_purchase, "Nabava")
        self.documents = LazyPage(_page_documents, "Dokumenti")
        self.crm = LazyPage(_page_crm, "CRM")
        self.reports = LazyPage(_page_reports, "Poročila")
        self.travel_orders = LazyPage(_page_travel_orders, "Potni nalogi")
        self.automation = LazyPage(_page_automation, "Avtomatizacija")

        self.stack.addWidget(self.dashboard)          # 0
        self.stack.addWidget(self.invoices)           # 1
        self.stack.addWidget(self.customers)          # 2
        self.stack.addWidget(self.offers)             # 3
        self.stack.addWidget(self.articles)           # 4
        self.stack.addWidget(self.company)            # 5
        self.stack.addWidget(self.payments)           # 6
        self.stack.addWidget(self.analytics)          # 7
        self.stack.addWidget(self.settings)           # 8
        self.stack.addWidget(self.orders)             # 9
        self.stack.addWidget(self.warehouse)          # 10
        self.stack.addWidget(self.suppliers)          # 11
        self.stack.addWidget(self.purchase)           # 12
        self.stack.addWidget(self.documents)          # 13
        self.stack.addWidget(self.crm)                # 14
        self.stack.addWidget(self.reports)            # 15
        self.stack.addWidget(self.automation)         # 16
        self.stack.addWidget(self.travel_orders)      # 17

        right_layout.addWidget(self.stack)
        root_layout.addWidget(right)
        self.setStatusBar(StatusBar())
        from app.core.ui.shortcuts import install_shortcuts
        install_shortcuts(self)

        self.sidebar.page_changed.connect(self.change_page)
        self.toolbar.new_invoice_clicked.connect(lambda: self.invoices.new_invoice())
        self.toolbar.new_offer_clicked.connect(lambda: self.offers.new_offer())
        self.toolbar.new_order_clicked.connect(lambda: self.orders.new_order())
        self.toolbar.new_customer_clicked.connect(lambda: self.customers.new_customer())
        self.toolbar.settings_clicked.connect(lambda: self.change_page(8))
        self.toolbar.lock_clicked.connect(self._manual_lock)
        self.toolbar.search_changed.connect(self._on_toolbar_search)
        self.toolbar.search_activated.connect(self._on_toolbar_search_activated)
        self.toolbar.set_context(0)
        apply_native_titlebar_theme(self, theme_manager.mode)

        self.dashboard.new_invoice_requested.connect(lambda: self.invoices.new_invoice())
        self.dashboard.new_customer_requested.connect(lambda: self.customers.new_customer())
        self.dashboard.new_article_requested.connect(lambda: self.articles.new_article())
        self.dashboard.new_offer_requested.connect(lambda: self.offers.new_offer())

        # Defer status chips (company/DB) until after first paint.
        from app.core.async_load import defer

        defer(self.statusBar().refresh)

    def change_page(self, index):
        from app.core.async_load import defer
        from app.core.permissions import can_open_page
        from app.core.session import session
        from app.core.ui.notify import toast

        if not can_open_page(index):
            toast(self, "Ni dovoljenja za ta modul.")
            return
        session.touch()

        # Build lazy page shell before the stack switch so navigation does not
        # flash an empty placeholder. Data refresh runs on the next tick.
        page = self.stack.widget(index)
        current = self.stack.currentWidget()
        if current is not None and current is not page:
            leave_target = current
            if isinstance(current, LazyPage) and current.is_loaded:
                leave_target = current.ensure()
            guard = getattr(leave_target, "confirm_leave", None)
            if callable(guard) and not guard():
                return

        first_lazy_load = isinstance(page, LazyPage) and not page.is_loaded
        if first_lazy_load:
            page.ensure()

        # Switch the stack first so navigation paints immediately, then refresh.
        self.setUpdatesEnabled(False)
        try:
            self.stack.setCurrentIndex(index)
            self.toolbar.set_context(index)
            self.sidebar.set_active(index)
        finally:
            self.setUpdatesEnabled(True)

        defer(lambda idx=index, first=first_lazy_load: self._finish_page_change(idx, first))

    def _finish_page_change(self, index: int, first_lazy_load: bool = False) -> None:
        # Drop stale deferred callbacks from rapid navigation so we do not
        # refresh modules the user already left (settings/license/DB work).
        if self.stack.currentIndex() != index:
            return
        self._refresh_page(index, skip_deferred_initial=first_lazy_load)
        bar = self.statusBar()
        if hasattr(bar, "refresh"):
            bar.refresh()
        from app.core.recovery import save_ui_session

        save_ui_session({"page": index})

    def _refresh_page(self, index: int, *, skip_deferred_initial: bool = False) -> None:
        if index == 0:
            self.dashboard.refresh()
        elif index == 1:
            self.invoices.refresh()
        elif index == 2:
            self.customers.refresh()
        elif index == 3:
            if hasattr(self.offers, "refresh"):
                self.offers.refresh()
        elif index == 4:
            self.articles.refresh()
        elif index == 5:
            self.company.refresh()
        elif index == 6:
            self.payments.refresh()
        elif index == 7:
            self.analytics.refresh()
        elif index == 8:
            # Settings shell paints first; showEvent owns the initial data load.
            if skip_deferred_initial:
                return
            self.settings.refresh()
        elif index == 9:
            self.orders.refresh()
        elif index == 10:
            self.warehouse.refresh()
        elif index == 11:
            self.suppliers.refresh()
        elif index == 12:
            self.purchase.refresh()
        elif index == 13:
            self.documents.refresh()
        elif index == 14:
            self.crm.refresh()
        elif index == 15:
            self.reports.refresh()
        elif index == 16:
            self.automation.refresh()
        elif index == 17:
            self.travel_orders.refresh()

    def _on_toolbar_search(self, text: str) -> None:
        """Forward shell search text to the active module filter field."""
        from PySide6.QtWidgets import QLineEdit

        page = self._current_page(ensure=False)
        if page is None:
            return
        search = getattr(page, "search", None)
        if isinstance(search, QLineEdit) and search.text() != text:
            search.setText(text)

    def _on_toolbar_search_activated(self, text: str) -> None:
        """Enter: focus page search if present, otherwise open command palette."""
        from PySide6.QtWidgets import QLineEdit

        from app.core.ui.command_palette import CommandPalette

        page = self._current_page(ensure=True)
        search = getattr(page, "search", None) if page is not None else None
        if isinstance(search, QLineEdit):
            if search.text() != text:
                search.setText(text)
            search.setFocus()
            search.selectAll()
            return
        dialog = CommandPalette(self)
        if dialog.exec():
            index = dialog.chosen_index()
            if index is not None:
                self.change_page(index)

    def _current_page(self, *, ensure: bool = True):
        page = self.stack.currentWidget()
        if isinstance(page, LazyPage):
            if not page.is_loaded and not ensure:
                return None
            return page.ensure()
        return page

    def _manual_lock(self) -> None:
        from app.core.idle_guard import get_idle_guard
        from app.core.session import session

        guard = get_idle_guard()
        if guard is not None:
            guard.lock_now()
            return
        if not session.authenticated:
            return
        from app.windows.unlock_dialog import UnlockDialog

        session.lock()
        unlock = UnlockDialog(self)
        if unlock.exec() != QDialog.DialogCode.Accepted:
            import sys

            sys.exit(0)
        self.sidebar.apply_role()
        self.toolbar.set_context(self.stack.currentIndex())
        self.statusBar().refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        from app.core.ui.app_identity import apply_native_titlebar_theme
        from app.theme.theme import theme_manager

        apply_native_titlebar_theme(self, theme_manager.mode)

    def closeEvent(self, event) -> None:
        """MainWindow is the sole quit authority — PDF viewers must not end the app."""
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            # Allow quit now that the user explicitly closes the main window.
            app.setQuitOnLastWindowClosed(True)
        super().closeEvent(event)


def _page_invoices():
    from app.modules.invoices import InvoicePage
    return InvoicePage()


def _page_customers():
    from app.modules.customers import CustomerPage
    return CustomerPage()


def _page_offers():
    from app.modules.offers.offer_page import OfferPage
    return OfferPage()


def _page_articles():
    from app.modules.articles import ArticlePage
    return ArticlePage()


def _page_company():
    from app.modules.company.company_page import CompanyPage
    return CompanyPage()


def _page_orders():
    from app.modules.orders import OrderPage
    return OrderPage()


def _page_analytics():
    from app.modules.analytics import AnalyticsView
    return AnalyticsView()


def _page_payments():
    from app.modules.payments import PaymentPage
    return PaymentPage()


def _page_settings():
    from app.modules.settings import SettingsPage
    return SettingsPage()


def _page_warehouse():
    from app.modules.warehouse import WarehousePage
    return WarehousePage()


def _page_suppliers():
    from app.modules.suppliers import SuppliersPage
    return SuppliersPage()


def _page_purchase():
    from app.modules.purchase import PurchasePage
    return PurchasePage()


def _page_documents():
    from app.modules.documents import DocumentsPage
    return DocumentsPage()


def _page_crm():
    from app.modules.crm import CrmPage
    return CrmPage()


def _page_reports():
    from app.modules.reports import ReportsPage
    return ReportsPage()


def _page_automation():
    from app.modules.automation import AutomationPage
    return AutomationPage()


def _page_travel_orders():
    from app.modules.travel_orders import TravelOrderPage
    return TravelOrderPage()


def _qt_message(mode, _context, message: str) -> None:
    if mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        logger.error("Qt: %s", message)
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning("Qt: %s", message)
    else:
        logger.debug("Qt: %s", message)


def run():
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QGuiApplication, QPixmapCache
    from PySide6.QtWidgets import QSplashScreen

    from app.core.perf import PerfSpan

    span = PerfSpan("startup")
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    install_excepthook()
    qInstallMessageHandler(_qt_message)
    existing = QApplication.instance()
    if existing is not None:
        # A leftover QApplication (failed prior start in-process) makes the UI appear "dead".
        logger.error("QApplication že obstaja — prekinjen zagon.")
        sys.exit(1)
    from app.core.app_mutex import acquire_app_mutex

    acquire_app_mutex()
    app = QApplication(sys.argv)
    from app.services.license_gate import ensure_licensed
    if not ensure_licensed():
        return 1
    # False until MainWindow is shown so UnlockDialog can run without a main window.
    app.setQuitOnLastWindowClosed(False)
    from app.core.ui.app_identity import apply_application_identity

    apply_application_identity(app)
    QPixmapCache.setCacheLimit(20 * 1024)
    # Apply persisted appearance BEFORE any visible window (fixes light→dark flash).
    from app.modules.settings.settings_controller import SettingsController

    settings = SettingsController()
    mode_name = settings.apply_appearance(app)
    span.mark("theme")
    from app.core.ui.splash_branding import build_splash_pixmap

    splash_pix, splash_fg = build_splash_pixmap(mode_name)
    splash = QSplashScreen(splash_pix)
    splash.setWindowIcon(app.windowIcon())
    splash.showMessage(
        "Zagon…",
        Qt.AlignBottom | Qt.AlignHCenter,
        splash_fg,
    )
    splash.show()
    app.processEvents()
    span.mark("splash")
    from app.core.update import apply_schema_upgrade
    apply_schema_upgrade()
    from app.core.db_guard import ensure_runtime
    from app.core.recovery import load_ui_session, mark_running
    crashed = mark_running()
    if crashed:
        from app.core.db_guard import integrity_ok
        if not integrity_ok():
            logger.error("Baza po sesutju ni konsistentna.")
    else:
        try:
            ensure_runtime()
        except Exception as exc:
            logger.error("Preverjanje baze: %s", exc)
    span.mark("database")
    from app.core.setup_state import needs_first_run
    if needs_first_run():
        from app.core.ui.app_identity import apply_native_titlebar_theme
        from app.theme.colors import ThemeMode
        from app.windows.first_run_wizard import FirstRunWizard

        wizard = FirstRunWizard()
        apply_native_titlebar_theme(
            wizard,
            ThemeMode.DARK if mode_name == "dark" else ThemeMode.LIGHT,
        )
        splash.hide()
        if wizard.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        splash.show()
        app.processEvents()
    extras = settings.load_extras()
    from app.core.auth_gate import (
        ensure_auth_migrated,
        needs_credential_onboarding,
        password_is_configured,
        startup_requires_authentication,
    )

    extras = ensure_auth_migrated(extras)

    # Legacy installs: setup_complete but no usable password — force onboarding
    # without touching business data. Idempotent once credentials exist.
    if needs_credential_onboarding(extras):
        splash.hide()
        from app.core.ui.app_identity import apply_native_titlebar_theme
        from app.theme.colors import ThemeMode
        from app.windows.credential_onboarding_dialog import CredentialOnboardingDialog

        onboard = CredentialOnboardingDialog()
        apply_native_titlebar_theme(
            onboard,
            ThemeMode.DARK if mode_name == "dark" else ThemeMode.LIGHT,
        )
        if onboard.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        extras = settings.load_extras()
        splash.show()
        app.processEvents()

    # After setup/onboarding, credentials must exist. Never auto-login Administrator.
    if not password_is_configured(extras):
        logger.error("Prijava ni nastavljena — zagon prekinjen.")
        sys.exit(0)

    if startup_requires_authentication(extras):
        splash.hide()
        from app.core.ui.app_identity import apply_native_titlebar_theme
        from app.theme.colors import ThemeMode
        from app.windows.unlock_dialog import UnlockDialog

        unlock = UnlockDialog()
        apply_native_titlebar_theme(
            unlock,
            ThemeMode.DARK if mode_name == "dark" else ThemeMode.LIGHT,
        )
        if unlock.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        splash.show()
        app.processEvents()
    span.mark("auth")
    extras = settings.load_extras()
    splash.showMessage(
        "Nalaganje delovne površine…",
        Qt.AlignBottom | Qt.AlignCenter,
        splash_fg,
    )
    app.processEvents()
    window = MainWindow()
    span.mark("window")
    window.show()
    app.processEvents()
    splash.finish(window)
    span.mark("shown")
    saved = load_ui_session()
    page = saved.get("page")
    if crashed and isinstance(page, int) and 0 <= page <= 17:
        window.change_page(page)

    def _background() -> None:
        from app.core.db_guard import maybe_vacuum
        from app.core.logger import cleanup_old_logs
        from app.core.module_cache import warmup
        from app.core.perf import log_snapshot
        from app.core.search_engine import ensure_search_schema
        from app.core.thumbs import cleanup_temp

        cleanup_temp()
        cleanup_old_logs()
        ensure_search_schema()
        try:
            maybe_vacuum()
        except Exception:
            pass
        warmup()
        log_snapshot("warmup")

    QTimer.singleShot(0, _background)
    from app.core.idle_guard import install_idle_guard

    # Keep False after MainWindow is shown. External PDF viewers / transient
    # toasts must never trigger lastWindowClosed quit. MainWindow.closeEvent
    # re-enables quit when the user explicitly closes the application.
    app.setQuitOnLastWindowClosed(False)
    timeout_sec = max(5, int(extras.get("session_timeout_min") or 30)) * 60

    install_idle_guard(
        app,
        window,
        password_required=password_is_configured(extras),
        timeout_sec=timeout_sec,
    )
    logger.info("%s", span.summary())
    sys.exit(app.exec())




