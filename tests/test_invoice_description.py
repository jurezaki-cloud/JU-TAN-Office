"""Article description survives invoice storage and reaches the rendered PDF."""
import uuid

import fitz
from reportlab.platypus import SimpleDocTemplate

from app.database.article_repository import article_repository
from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.modules.invoices.invoice_dialog import InvoiceDialog
from app.modules.invoices.invoice_item_dialog import InvoiceItemDialog
from app.pdf.pdf_export import _items
from app.pdf.pdf_tables import build_items_table


def test_description_from_article_to_saved_invoice_and_pdf(qt_app, tmp_path, monkeypatch):
    tag = uuid.uuid4().hex[:8]
    description = 'Vzdrževanje omrežij & CRM <premium>\nMesečna podpora'
    article_repository.add(tag, 'Storitev', description, 'mes', 100, 0)
    aid = next(a[0] for a in article_repository.get_all() if a[1] == tag)
    customer_repository.add(f'Description {tag}', '', '', '', '', 'SI', '', '', '')
    cid = customer_repository.search(f'Description {tag}')[0][0]
    item_dialog = InvoiceItemDialog(vat_liable=False)
    item_dialog.article.setCurrentIndex(next(i for i in range(item_dialog.article.count()) if item_dialog.article.itemData(i)[0] == aid))
    assert item_dialog.description.toPlainText() == description
    item_dialog.description.appendPlainText('Dogovorjen obseg')
    row = item_dialog.get_data()
    assert row[9] == description + '\nDogovorjen obseg'
    # Exercise the actual save/load path with write authorization isolated from login.
    monkeypatch.setattr('app.core.permissions.allow', lambda *args, **kwargs: True)
    monkeypatch.setattr('app.core.permissions.audit', lambda *args, **kwargs: None)
    dialog = InvoiceDialog()
    dialog.customer.setCurrentIndex(dialog.customer.findData(cid))
    dialog.items_model.add_item(row)
    dialog.save()
    assert dialog.invoice_id is not None
    stored = invoice_repository.get_items(dialog.invoice_id)
    assert stored[0][4] == row[9]
    loaded = InvoiceDialog(invoice_id=dialog.invoice_id)
    assert loaded.items_model.items[0][9] == row[9]
    items = _items(stored)
    assert items[0]['unit'] == 'mes'
    path = tmp_path / 'description.pdf'
    SimpleDocTemplate(str(path)).build([build_items_table(items, {})])
    with fitz.open(path) as pdf:
        text = '\n'.join(page.get_text() for page in pdf)
    for part in ('Storitev', 'Vzdrževanje omrežij & CRM <premium>', 'Mesečna podpora', 'Dogovorjen obseg', 'mes'):
        assert ''.join(part.split()) in ''.join(text.split())


def test_empty_description_remains_compatible_with_legacy_rows():
    items = _items([(1, None, 'A', 'Storitev', None, 1, 'kos', 100, 0, 0, 100)])
    cell = build_items_table(items, {}).table._cellvalues[1][1]
    assert cell.getPlainText() == 'Storitev'
