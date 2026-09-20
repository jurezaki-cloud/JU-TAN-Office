"""Responsive UI framework + content-sized dialogs."""

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QTableView

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.sizes import (
    FOOTER_HEIGHT,
    SIZE_PRESETS,
    TABLE_MAX_HEIGHT,
    apply_dialog_table,
    dialog_table_height,
    fit_size,
    recommend_preset,
)
from app.modules.articles.article_dialog import ArticleDialog
from app.modules.customers.customer_dialog import CustomerDialog
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.modules.offers.offer_dialog import OfferDialog


def test_fit_never_fullscreen_across_resolutions():
    cases = [
        (QRect(0, 0, 1366, 768), "SMALL"),
        (QRect(0, 0, 1600, 900), "MEDIUM"),
        (QRect(0, 0, 1920, 1080), "MEDIUM"),
        (QRect(0, 0, 2560, 1440), "LARGE"),
        (QRect(0, 0, 3840, 2160), "XL"),
    ]
    for area, expected in cases:
        assert recommend_preset(area) == expected
        fitted = fit_size(SIZE_PRESETS["XL"], area)
        assert fitted.width() <= int(area.width() * 0.90)
        assert fitted.height() <= int(area.height() * 0.85)
        assert fitted.width() < area.width()
        assert fitted.height() < area.height()


def test_dpi_scale_keeps_dialogs_inside_screen():
    for scale in (1.0, 1.25, 1.5, 1.75, 2.0):
        logical = QRect(0, 0, int(1920 / scale), int(1080 / scale))
        fitted = fit_size(SIZE_PRESETS["MEDIUM"], logical)
        assert fitted.width() < logical.width()
        assert fitted.height() < logical.height()


def test_enterprise_dialog_scroll_footer_table(qt_app):
    dialog = EnterpriseDialog(title="QA", size="SMALL")
    assert dialog.scroll is not None
    assert dialog.footer.height() == FOOTER_HEIGHT or dialog.footer.minimumHeight() == FOOTER_HEIGHT
    assert not dialog.footer.isHidden()
    table = QTableView()
    dialog.body.addWidget(table)
    dialog.bind_table(table)
    assert table.maximumHeight() <= TABLE_MAX_HEIGHT
    assert table.minimumHeight() < 200
    area = QGuiApplication.primaryScreen().availableGeometry() if QGuiApplication.primaryScreen() else QRect(0, 0, 1920, 1080)
    dialog.show()
    qt_app.processEvents()
    dialog.fit_to_content()
    assert dialog.footer.isVisible()
    assert dialog.width() < area.width()
    assert dialog.height() < area.height()
    assert dialog.height() <= int(area.height() * 0.85) + 1
    dialog.close()


def test_table_height_follows_row_count(qt_app):
    empty = QTableView()
    apply_dialog_table(empty)
    compact = dialog_table_height(empty)
    assert compact < 200
    assert empty.maximumHeight() == compact


def test_dialogs_open_to_content_not_preset(qt_app):
    area = QGuiApplication.primaryScreen().availableGeometry() if QGuiApplication.primaryScreen() else QRect(0, 0, 1920, 1080)
    for factory in (CustomerDialog, ArticleDialog, InvoiceDialog, OfferDialog):
        dialog = factory()
        dialog.show()
        qt_app.processEvents()
        dialog.fit_to_content()
        assert dialog.width() < area.width()
        assert dialog.height() < area.height()
        assert dialog.height() < SIZE_PRESETS["LARGE"].height()
        assert dialog.footer.isVisible()
        dialog.close()


def test_customer_dialog_uses_framework(qt_app):
    dialog = CustomerDialog()
    assert isinstance(dialog, EnterpriseDialog)
    dialog.form.company.setText("UI d.o.o.")
    assert dialog.get_data()["company"] == "UI d.o.o."
    dialog.close()
