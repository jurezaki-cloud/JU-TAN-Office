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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.lazy_page import LazyPage
from app.core.logger import install_excepthook, logger
from app.theme import theme_manager
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
        self.setWindowTitle("JU-TAN Office Enterprise")
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
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(16)

        self.toolbar = ModernToolbar()
        right_layout.addWidget(self.toolbar)

        self.stack = QStackedWidget()

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
        self.automation = LazyPage(_page_automation, "Automation")
        self.travel_orders = LazyPage(_page_travel_orders, "Potni nalogi")

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
        self.statusBar().refresh()

        self.sidebar.page_changed.connect(self.change_page)
        self.toolbar.new_invoice_clicked.connect(lambda: self.invoices.new_invoice())
        self.toolbar.new_customer_clicked.connect(lambda: self.customers.new_customer())
        self.toolbar.settings_clicked.connect(lambda: self.change_page(8))
        self.toolbar.search_changed.connect(self._toolbar_search)
        self.toolbar.set_context(0)

        self.dashboard.new_invoice_requested.connect(lambda: self.invoices.new_invoice())
        self.dashboard.new_customer_requested.connect(lambda: self.customers.new_customer())
        self.dashboard.new_article_requested.connect(lambda: self.articles.new_article())
        self.dashboard.new_offer_requested.connect(lambda: self.offers.new_offer())

    def change_page(self, index):
        from app.core.permissions import can_open_page
        from app.core.ui.notify import toast

        if not can_open_page(index):
            toast(self, "Ni dovoljenja za ta modul.")
            return
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
        elif index == 6:
            self.payments.refresh()
        elif index == 7:
            self.analytics.refresh()
        elif index == 8:
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

        self.stack.setCurrentIndex(index)
        self.toolbar.set_context(index)
        self.sidebar.set_active(index)
        bar = self.statusBar()
        if hasattr(bar, "refresh"):
            bar.refresh()
        from app.core.recovery import save_ui_session
        save_ui_session({"page": index})

    def _toolbar_search(self, text: str):
        page = self.stack.currentWidget()
        search = getattr(page, "search", None)
        if search is not None and hasattr(search, "setText"):
            search.setText(text)


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
    from PySide6.QtCore import QEvent, QObject, Qt, QTimer
    from PySide6.QtGui import QColor, QGuiApplication, QPixmap, QPixmapCache
    from PySide6.QtWidgets import QSplashScreen

    from app.core.perf import PerfSpan

    span = PerfSpan("startup")
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    install_excepthook()
    qInstallMessageHandler(_qt_message)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    QPixmapCache.setCacheLimit(20 * 1024)
    splash_pix = QPixmap(420, 200)
    splash_pix.fill(QColor("#0F172A"))
    splash = QSplashScreen(splash_pix)
    splash.showMessage(
        "JU-TAN Office Enterprise",
        Qt.AlignBottom | Qt.AlignCenter,
        QColor("#F8FAFC"),
    )
    splash.show()
    app.processEvents()
    span.mark("splash")
    theme_manager.apply(app)
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
        from app.windows.first_run_wizard import FirstRunWizard
        wizard = FirstRunWizard()
        splash.hide()
        if wizard.exec() != wizard.Accepted:
            sys.exit(0)
        splash.show()
        app.processEvents()
    from app.modules.settings.settings_controller import SettingsController
    extras = SettingsController().load_extras()
    if extras.get("password_hash"):
        splash.hide()
        from app.windows.unlock_dialog import UnlockDialog
        unlock = UnlockDialog()
        if unlock.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        splash.show()
        app.processEvents()
    else:
        from app.core.session import session
        session.remember_user = bool(extras.get("remember_user", True))
        session.login(
            extras.get("administrator") or "Administrator",
            extras.get("role") or "Administrator",
        )
    window = MainWindow()
    span.mark("window")
    window.show()
    splash.finish(window)
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
    from app.core.session import session as app_session
    app_session.timeout_sec = int(extras.get("session_timeout_min") or 30) * 60

    class _Idle(QObject):
        def eventFilter(self, _obj, event):
            if event.type() in (QEvent.MouseMove, QEvent.KeyPress, QEvent.MouseButtonPress):
                app_session.touch()
            return False

    idle = _Idle(app)
    app.installEventFilter(idle)

    def _tick():
        if extras.get("password_hash") and app_session.idle_too_long() and not app_session.locked:
            app_session.lock()
            from app.windows.unlock_dialog import UnlockDialog
            dlg = UnlockDialog(window)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                sys.exit(0)

    lock_timer = QTimer(window)
    lock_timer.timeout.connect(_tick)
    lock_timer.start(15000)
    logger.info("%s", span.summary())
    sys.exit(app.exec())




