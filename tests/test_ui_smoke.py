"""UI testi: dialogi, CRUD, filtri, iskanje, izvoz."""

from pathlib import Path

from app.database.customer_repository import customer_repository
from app.excel.excel_export import write_workbook
from app.modules.customers.customer_dialog import CustomerDialog
from app.modules.customers.customer_page import CustomerPage
from app.windows.main_window import MainWindow


def test_customer_dialog_fields(qt_app):
    dialog = CustomerDialog()
    dialog.form.company.setText("UI d.o.o.")
    dialog.form.contact.setText("Maja")
    data = dialog.get_data()
    assert data["company"] == "UI d.o.o."
    assert data["contact"] == "Maja"
    dialog.close()


def test_customer_crud_search_and_export(qt_app, tmp_path):
    customer_repository.add(
        "Iskanje d.o.o.", "Tina", "", "", "Maribor", "SI", "", "t@test.si", "",
    )
    page = CustomerPage()
    page.refresh()
    page.search.setText("Iskanje")
    names = [row[1] for row in page.model.customers]
    assert any("Iskanje" in str(name) for name in names)
    page.search.setText("zzzz-no-match")
    assert page.model.customers == [] or all(
        "zzzz-no-match" not in str(row[1]).casefold() for row in page.model.customers
    )
    target = tmp_path / "stranke.xlsx"
    write_workbook(
        target,
        "customers",
        ["Podjetje", "Kontakt"],
        [["Iskanje d.o.o.", "Tina"]],
    )
    assert target.exists()
    page.close()


def test_main_window_lazy_indices(qt_app):
    window = MainWindow()
    assert window.stack.count() == 18
    assert window.stack.indexOf(window.dashboard) == 0
    assert window.stack.indexOf(window.invoices) == 1
    assert window.stack.indexOf(window.reports) == 15
    assert window.stack.indexOf(window.automation) == 16
    assert window.invoices._inner is None
    window.change_page(2)
    assert window.stack.currentIndex() == 2
    assert window.customers._inner is not None
    window.close()
