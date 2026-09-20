import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
)

from app.widgets.sidebar import Sidebar
from app.widgets.toolbar import TopToolbar
from app.widgets.statusbar import StatusBar

from app.windows.dashboard import Dashboard
from app.windows.offers import Offers
from app.windows.invoices import Invoices, Payments
from app.windows.analytics import Analytics
from app.windows.settings import Settings
from app.utils.theme import apply_theme

from app.modules.customers import CustomerPage
from app.modules.articles import ArticlePage


def _license_client():
    from app.licensing.client import LicenseClient
    from app.licensing.config import LICENSE_PUBLIC_KEY, LICENSE_SERVER_URL
    from app.licensing.verifier import LicenseVerifier

    return LicenseClient(
        LICENSE_SERVER_URL,
        LicenseVerifier(LICENSE_PUBLIC_KEY),
    )


class EmptyPage(QWidget):

    def __init__(self, title):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(title)
        label.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        layout.addWidget(label)
        layout.addStretch()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("JU-TAN Office Enterprise")
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        # Desni del
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 12, 24, 20)
        right_layout.setSpacing(0)

        self.toolbar = TopToolbar()
        right_layout.addWidget(self.toolbar)

        # Strani
        self.stack = QStackedWidget()

        self.dashboard = Dashboard()
        self.customers = CustomerPage()
        self.articles = ArticlePage()
        self.offers = Offers()
        self.invoices = Invoices()
        self.payments = Payments()
        self.analytics = Analytics()
        self.settings = Settings()

        self.stack.addWidget(self.dashboard)                 # 0
        self.stack.addWidget(self.invoices)                  # 1
        self.stack.addWidget(self.customers)                 # 2
        self.stack.addWidget(self.offers)                    # 3
        self.stack.addWidget(EmptyPage("Storitve"))          # 4
        self.stack.addWidget(self.articles)                  # 5
        self.stack.addWidget(self.payments)                  # 6
        self.stack.addWidget(self.analytics)                 # 7
        self.stack.addWidget(self.settings)                  # 8

        right_layout.addWidget(self.stack)

        root_layout.addWidget(right)

        self.setStatusBar(StatusBar())

        self.sidebar.page_changed.connect(self.change_page)

    def change_page(self, index):

        if index == 0:
            self.dashboard.refresh()

        elif index == 1:
            self.invoices.refresh()

        elif index == 2:
            self.customers.refresh()

        elif index == 3:
            self.offers.refresh()

        elif index == 5:
            self.articles.refresh()

        elif index == 6:
            self.payments.refresh()

        elif index == 7:
            self.analytics.refresh()

        elif index == 8:
            self.settings.load()

        self.stack.setCurrentIndex(index)
        self.sidebar.set_active(index)
        self.toolbar.set_page(index)


def run():

    app = QApplication(sys.argv)
    apply_theme(app)

    from app.licensing.config import LICENSE_PUBLIC_KEY, LICENSE_REQUIRED
    if LICENSE_REQUIRED:
        from PySide6.QtWidgets import QMessageBox
        from app.licensing.dialog import ensure_licensed

        if not LICENSE_PUBLIC_KEY:
            QMessageBox.critical(
                None,
                "Licenčna konfiguracija",
                "Program nima nastavljenega javnega licenčnega ključa. "
                "Obrnite se na podporo JU-TAN.",
            )
            return 2
        state = ensure_licensed(_license_client())
        if not state.permits_use:
            QMessageBox.critical(None, "Licenca", state.message)
            return 3

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
