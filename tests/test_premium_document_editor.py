"""Regression tests for premium document-editor CTA visibility and PDF polish."""

from __future__ import annotations

from pathlib import Path

from app.pdf.pdf_branding import extract_signer_name


def test_extract_signer_rejects_studio_brand_label():
    assert extract_signer_name("JU-TAN studio") == ""
    assert extract_signer_name("JU-TAN studio, Tanja Hrup s.p.") == "Tanja Hrup"
    assert extract_signer_name("Acme d.o.o., Janez Novak s.p.") == "Janez Novak"


def test_theme_qss_does_not_force_transparent_buttons_in_document_splitter():
    qss = Path("app/theme/theme.qss").read_text(encoding="utf-8")
    # Broad transparent paint on every QWidget under the splitter washed out
    # PrimaryButton fills (white text on transparent = invisible CTA).
    assert "#DocumentEditorSplitter QWidget" not in qss
    assert "#DocumentItemsPanel QPushButton#PrimaryButton" in qss
    assert "QFrame#DocumentItemsPanel" in qss
    assert "QFrame#DocumentItemsEmpty" in qss


def test_document_items_panel_primary_cta_and_empty_state(qt_app):
    from app.theme.theme import theme_manager
    from app.widgets.document_editor.items_panel import DocumentItemsPanel

    theme_manager.apply(qt_app)

    panel = DocumentItemsPanel()
    panel.show()
    qt_app.processEvents()

    assert panel.btn_add_item.objectName() == "PrimaryButton"
    assert panel.btn_remove_item.objectName() == "DangerButton"
    assert panel.content_stack.currentWidget() is panel.empty_state

    panel.set_add_enabled(False, reason="Najprej izberite stranko.")
    assert not panel.btn_add_item.isEnabled()
    assert not panel.btn_empty_add.isEnabled()
    assert panel.lbl_add_hint.isVisible()
    assert "stranko" in panel.lbl_add_hint.text().casefold()

    panel.set_add_enabled(True)
    assert panel.btn_add_item.isEnabled()
    assert panel.btn_empty_add.isEnabled()
    assert not panel.lbl_add_hint.isVisible()

    panel.set_item_count(1)
    assert panel.content_stack.currentWidget() is not panel.empty_state
    assert "1 postavka" in panel.lbl_count.text()
    panel.close()


def test_invoice_items_model_numeric_alignment_and_formatting():
    from PySide6.QtCore import Qt

    from app.modules.invoices.models.invoice_items_model import InvoiceItemsModel

    model = InvoiceItemsModel()
    model.refresh([["A-1", "Storitev", 2, "kos", 10.5, 5, 22, 24.52, 1]])

    index_price = model.index(0, 4)
    index_name = model.index(0, 1)
    assert "€" in model.data(index_price, Qt.DisplayRole)
    assert model.data(index_name, Qt.TextAlignmentRole) == int(Qt.AlignLeft | Qt.AlignVCenter)
    assert model.data(index_price, Qt.TextAlignmentRole) == int(Qt.AlignRight | Qt.AlignVCenter)
