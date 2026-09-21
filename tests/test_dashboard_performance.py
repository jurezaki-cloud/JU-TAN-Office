"""Phase 4 P1 — dashboard N+1 query regressions (output must stay identical)."""

from __future__ import annotations

from datetime import date, timedelta

from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.payment_repository import payment_repository
from app.widgets.invoices.status_badge import invoice_badge


TODAY = date.today().isoformat()
PAST = (date.today() - timedelta(days=10)).isoformat()


def _seed_customer(name: str) -> int:
    customer_repository.add(
        name, "Test", "", "1000", "Ljubljana", "SI", "", "dash-perf@t.si", "",
    )
    return customer_repository.search(name)[0][0]


def _seed_invoice(number: str, customer_id: int, total: float, status: str, due: str):
    return invoice_repository.add(
        number,
        customer_id,
        TODAY,
        due,
        float(total) / 1.22,
        0,
        float(total) - float(total) / 1.22,
        total,
        "",
        status,
    )


def _legacy_unpaid_overdue(invoices):
    """Mirror the pre-optimization dashboard loop for output parity checks."""
    unpaid = 0.0
    overdue = 0.0
    for row in invoices:
        full = invoice_repository.get_by_id(row[0])
        due = full[4] if full else None
        badge = invoice_badge(row[5], due)
        total = float(row[4] or 0)
        outstanding = payment_repository.remaining(row[0], total)
        if badge in ("Neplačano", "Delno plačano", "Zapadlo"):
            unpaid += outstanding
        if badge == "Zapadlo":
            overdue += outstanding
    return unpaid, overdue


def test_get_due_dates_map_matches_get_by_id():
    customer_id = _seed_customer("DASH DUE d.o.o.")
    a = _seed_invoice("RAC-DUE-A", customer_id, 122.0, "Izdan", PAST)
    b = _seed_invoice("RAC-DUE-B", customer_id, 50.0, "Izdan", TODAY)
    mapping = invoice_repository.get_due_dates_map([a, b, 999999])
    assert mapping[a] == PAST
    assert mapping[b] == TODAY
    assert 999999 not in mapping
    assert mapping[a] == invoice_repository.get_by_id(a)[4]
    assert mapping[b] == invoice_repository.get_by_id(b)[4]
    assert invoice_repository.get_due_dates_map([]) == {}


def test_remaining_map_matches_per_invoice_remaining():
    customer_id = _seed_customer("DASH REM d.o.o.")
    unpaid_id = _seed_invoice("RAC-REM-1", customer_id, 122.0, "Izdan", TODAY)
    partial_id = _seed_invoice("RAC-REM-2", customer_id, 200.0, "Izdan", TODAY)
    payment_repository.add(partial_id, TODAY, 50, "Nakazilo")
    payment_repository.sync_invoice_status(partial_id, 200.0)

    totals = {unpaid_id: 122.0, partial_id: 200.0}
    batch = payment_repository.remaining_map(totals)
    assert batch[unpaid_id] == payment_repository.remaining(unpaid_id, 122.0)
    assert batch[partial_id] == payment_repository.remaining(partial_id, 200.0)
    assert payment_repository.remaining_map({}) == {}
    assert payment_repository.sums_by_invoice_ids([]) == {}


def test_dashboard_kpi_parity_with_legacy_loop():
    customer_id = _seed_customer("DASH KPI d.o.o.")
    open_id = _seed_invoice("RAC-KPI-1", customer_id, 122.0, "Izdan", TODAY)
    overdue_id = _seed_invoice("RAC-KPI-2", customer_id, 80.0, "Izdan", PAST)
    partial_id = _seed_invoice("RAC-KPI-3", customer_id, 200.0, "Izdan", TODAY)
    payment_repository.add(partial_id, TODAY, 50, "Nakazilo")
    payment_repository.sync_invoice_status(partial_id, 200.0)
    _seed_invoice("RAC-KPI-4", customer_id, 10.0, "Plačan", TODAY)

    invoices = [
        row
        for row in invoice_repository.get_all()
        if row[0] in (open_id, overdue_id, partial_id) or str(row[1]).startswith("RAC-KPI")
    ]
    legacy_unpaid, legacy_overdue = _legacy_unpaid_overdue(invoices)

    due_dates = invoice_repository.get_due_dates_map([row[0] for row in invoices])
    remainings = payment_repository.remaining_map(
        {row[0]: float(row[4] or 0) for row in invoices}
    )
    unpaid = 0.0
    overdue = 0.0
    for row in invoices:
        badge = invoice_badge(row[5], due_dates.get(row[0]))
        outstanding = remainings.get(row[0], float(row[4] or 0))
        if badge in ("Neplačano", "Delno plačano", "Zapadlo"):
            unpaid += outstanding
        if badge == "Zapadlo":
            overdue += outstanding

    assert unpaid == legacy_unpaid
    assert overdue == legacy_overdue
    assert unpaid > 0
    assert overdue > 0


def test_dashboard_refresh_avoids_n_plus_one(qt_app, monkeypatch):
    customer_id = _seed_customer("DASH N1 d.o.o.")
    for index in range(5):
        _seed_invoice(
            f"RAC-N1-{index}",
            customer_id,
            100.0 + index,
            "Izdan",
            PAST if index % 2 else TODAY,
        )

    get_calls = {"n": 0}
    remaining_calls = {"n": 0}
    real_get = invoice_repository.get_by_id
    real_remaining = payment_repository.remaining

    def counting_get(invoice_id):
        get_calls["n"] += 1
        return real_get(invoice_id)

    def counting_remaining(invoice_id, invoice_total):
        remaining_calls["n"] += 1
        return real_remaining(invoice_id, invoice_total)

    monkeypatch.setattr(invoice_repository, "get_by_id", counting_get)
    monkeypatch.setattr(payment_repository, "remaining", counting_remaining)

    from app.windows.dashboard import Dashboard

    dash = Dashboard()
    dash.refresh()

    # Refresh must use batch helpers — not one get_by_id/remaining per invoice.
    assert get_calls["n"] == 0
    assert remaining_calls["n"] == 0
    assert dash.invoice_table.rowCount() >= 1
    assert dash._invoices_stack.currentWidget() is dash.invoice_table


def test_dashboard_empty_states(qt_app, monkeypatch):
    from app.database.offer_repository import offer_repository

    monkeypatch.setattr(invoice_repository, "get_all", lambda: [])
    monkeypatch.setattr(offer_repository, "get_all", lambda: [])
    monkeypatch.setattr(customer_repository, "get_all", lambda: [])
    monkeypatch.setattr(invoice_repository, "get_total_revenue", lambda: 0)
    monkeypatch.setattr(invoice_repository, "get_due_dates_map", lambda _ids=None: {})
    monkeypatch.setattr(payment_repository, "remaining_map", lambda _totals: {})
    monkeypatch.setattr(invoice_repository, "get_monthly_revenue", lambda: [])

    from app.windows.dashboard import Dashboard

    dash = Dashboard()
    dash.refresh()
    assert dash._invoices_stack.currentWidget() is dash._invoices_empty
    assert dash._activity_stack.currentWidget() is dash._activity_empty
    assert "Ni računov" in dash._invoices_empty.text()
    assert "Ni zadnjih aktivnosti" in dash._activity_empty.text()
