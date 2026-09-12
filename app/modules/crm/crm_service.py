from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.database.customer_repository import customer_repository
from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import offer_repository
from app.database.order_repository import order_repository
from app.modules.crm.crm_repository import (
    ACTIVITY_TYPES,
    PRIORITIES,
    STAGES,
    crm_repository,
)
from app.modules.documents.documents_repository import documents_repository
from app.pdf.pdf_company import load_company
from app.widgets.invoices.status_badge import invoice_badge


class CrmService:
    def __init__(self, repository=crm_repository) -> None:
        self.repository = repository

    def default_owner(self) -> str:
        return (load_company().name or "JU-TAN").strip()

    def stages(self) -> tuple[str, ...]:
        return STAGES

    def activity_types(self) -> tuple[str, ...]:
        return ACTIVITY_TYPES

    def priorities(self) -> tuple[str, ...]:
        return PRIORITIES

    def create_lead(self, data: dict) -> int:
        company = (data.get("company") or "").strip()
        customer_id = data.get("customer_id") or self._match_customer(company)
        contact_id = self.repository.add_contact(
            customer_id=customer_id,
            company=company,
            contact=data.get("contact") or "",
            email=data.get("email") or "",
            phone=data.get("phone") or "",
            vat=data.get("vat") or "",
            salesperson=data.get("salesperson") or self.default_owner(),
        )
        return self.repository.add_deal(
            customer_id=customer_id,
            contact_id=contact_id,
            title=data.get("title") or company or "Lead",
            company=company,
            stage=data.get("stage") or "Lead",
            salesperson=data.get("salesperson") or self.default_owner(),
            priority=data.get("priority") or "Normal",
            value=data.get("value") or 0,
        )

    def add_activity(self, data: dict) -> int:
        activity_id = self.repository.add_activity(**data)
        if (data.get("type") or "") == "Note" and data.get("notes"):
            self.repository.add_note(
                data.get("customer_id"),
                data.get("pipeline_id"),
                data.get("notes") or data.get("title") or "",
                data.get("salesperson") or self.default_owner(),
            )
        return activity_id

    def set_stage(self, deal_id: int, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError("Neznan stage.")
        self.repository.set_stage(deal_id, stage)

    def filter_deals(
        self,
        salesperson: str = "all",
        status: str = "all",
        stage: str = "all",
        priority: str = "all",
        date_filter: str = "all",
        selected_date: str | None = None,
        query: str = "",
    ) -> list:
        text = query.strip().casefold()
        today = date.today()
        rows = []
        for deal in self.repository.deals():
            if salesperson not in ("all", "", None) and deal[6] != salesperson:
                continue
            if status not in ("all", "", None) and deal[9] != status:
                continue
            if stage not in ("all", "", None) and deal[5] != stage:
                continue
            if priority not in ("all", "", None) and deal[7] != priority:
                continue
            created = str(deal[10] or "")[:10]
            if date_filter == "today" and created != today.isoformat():
                continue
            if date_filter == "month" and not created.startswith(today.strftime("%Y-%m")):
                continue
            if date_filter == "day" and selected_date and created != selected_date:
                continue
            hay = f"{deal[3]} {deal[4]} {deal[6]}".casefold()
            if text and text not in hay:
                continue
            rows.append(deal)
        return rows

    def search_customers(self, query: str) -> list:
        text = query.strip().casefold()
        rows = []
        for customer in customer_repository.get_all():
            full = customer_repository.get_by_id(customer[0])
            if full is None:
                continue
            hay = " ".join(str(part or "") for part in full[1:10]).casefold()
            if text and text not in hay:
                continue
            rows.append(full)
        if text:
            for contact in self.repository.contacts():
                hay = " ".join(str(part or "") for part in contact[2:7]).casefold()
                if text not in hay:
                    continue
                if contact[1]:
                    continue
                rows.append((
                    None,
                    contact[2],
                    contact[3],
                    "",
                    "",
                    "",
                    "",
                    contact[6],
                    contact[4],
                    contact[5],
                ))
        return rows

    def customer_360(self, customer_id: int) -> dict[str, Any]:
        customer = customer_repository.get_by_id(customer_id)
        invoices = []
        offers = []
        orders = []
        revenue = 0.0
        open_total = 0.0
        for invoice in invoice_repository.get_all():
            full = invoice_repository.get_by_id(invoice[0])
            if full is None or full[2] != customer_id:
                continue
            invoices.append(invoice)
            try:
                total = float(invoice[4] or 0)
            except (TypeError, ValueError):
                total = 0.0
            revenue += total
            badge = invoice_badge(invoice[5], full[4] if len(full) > 4 else None)
            if badge in ("Neplačano", "Zapadlo", "Osnutek"):
                open_total += total
        for offer in offer_repository.get_all():
            full = offer_repository.get_by_id(offer[0])
            if full is not None and full[2] == customer_id:
                offers.append(offer)
        for order in order_repository.get_all():
            full = order_repository.get_by_id(order[0])
            if full is not None and full[2] == customer_id:
                orders.append(order)
        documents = []
        try:
            for doc in documents_repository.search(module="customer", scoped=False):
                if doc[11] == customer_id:
                    documents.append(doc)
        except Exception:
            documents = []
        activities = self.repository.activities(customer_id)
        notes = self.repository.notes(customer_id)
        timeline = self._timeline(invoices, offers, orders, activities, notes)
        return {
            "customer": customer,
            "revenue": revenue,
            "open_invoices": open_total,
            "invoices": invoices,
            "offers": offers,
            "orders": orders,
            "payments": [row for row in invoices if invoice_badge(row[5]) == "Plačano"],
            "documents": documents,
            "activities": activities,
            "notes": notes,
            "timeline": timeline,
        }

    def followups(self) -> dict[str, list]:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=(6 - today.weekday()))
        buckets = {"today": [], "tomorrow": [], "week": [], "overdue": []}
        for item in self.repository.activities():
            if item[9]:
                continue
            due = str(item[6] or "")[:10]
            if not due:
                continue
            try:
                when = date.fromisoformat(due)
            except ValueError:
                continue
            if when < today:
                buckets["overdue"].append(item)
            elif when == today:
                buckets["today"].append(item)
            elif when == tomorrow:
                buckets["tomorrow"].append(item)
            elif today < when <= week_end:
                buckets["week"].append(item)
        return buckets

    def kpis(self) -> dict:
        deals = self.repository.deals()
        today = date.today().isoformat()
        meetings = 0
        calls = 0
        for item in self.repository.activities():
            due = str(item[6] or item[11] or "")[:10]
            if due != today:
                continue
            if item[4] == "Meeting":
                meetings += 1
            if item[4] == "Call":
                calls += 1
        return {
            "leads": sum(1 for row in deals if row[5] == "Lead"),
            "active": sum(1 for row in deals if row[9] == "Active"),
            "won": sum(1 for row in deals if row[5] == "Won"),
            "lost": sum(1 for row in deals if row[5] == "Lost"),
            "meetings": meetings,
            "calls": calls,
        }

    def _match_customer(self, company: str):
        target = company.casefold()
        if not target:
            return None
        for row in customer_repository.get_all():
            if str(row[1] or "").strip().casefold() == target:
                return row[0]
        return None

    def _timeline(self, invoices, offers, orders, activities, notes) -> list[dict]:
        events = []
        for row in invoices:
            events.append({"date": str(row[2] or ""), "kind": "Invoice", "text": str(row[1])})
        for row in offers:
            events.append({"date": str(row[3] or ""), "kind": "Offer", "text": str(row[1])})
        for row in orders:
            events.append({"date": str(row[3] or ""), "kind": "Order", "text": str(row[1])})
        for row in activities:
            events.append({
                "date": str(row[6] or row[11] or "")[:19],
                "kind": str(row[4] or "Activity"),
                "text": str(row[5] or ""),
            })
        for row in notes:
            events.append({
                "date": str(row[5] or "")[:19],
                "kind": "Note",
                "text": str(row[3] or "")[:80],
            })
        events.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
        return events[:40]


crm_service = CrmService()
