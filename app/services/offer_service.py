"""Offer business rules (conversion, edit protection)."""

from __future__ import annotations

from datetime import date, timedelta

from app.database.invoice_repository import invoice_repository
from app.database.offer_repository import CONVERTED_OFFER_MESSAGE, offer_repository


class OfferService:

    def is_converted(self, offer_id) -> bool:
        return offer_repository.is_converted(offer_id)

    def converted_invoice_id(self, offer_id):
        return offer_repository.get_converted_invoice_id(offer_id)

    def assert_editable(self, offer_id) -> None:
        if offer_repository.is_converted(offer_id):
            raise ValueError(CONVERTED_OFFER_MESSAGE)

    def convert_to_invoice(self, offer_id) -> tuple[int, str]:
        """
        Create one invoice from an offer and lock the offer.

        Returns (invoice_id, invoice_number).
        Raises ValueError if the offer is missing, empty, or already converted.
        """
        offer = offer_repository.get_by_id(offer_id)
        if offer is None:
            raise ValueError("Ponudba ne obstaja.")

        if offer_repository.is_converted(offer_id):
            raise ValueError(
                "Ponudba je že pretvorjena v račun. Ponovna pretvorba ni dovoljena."
            )

        items = offer_repository.get_items(offer_id)
        if not items:
            raise ValueError("Ponudba nima postavk.")

        today = date.today()
        due = today + timedelta(days=30)
        notes = (offer[10] or "") + (f"\n[Iz ponudbe {offer[1]}]" if offer[1] else "")

        # Allocate a free invoice number (counter can lag if other flows
        # inserted numbers without bumping company.invoice_counter).
        import sqlite3

        invoice_id = None
        number = None
        for _ in range(50):
            number = invoice_repository.get_next_number()
            try:
                invoice_id = invoice_repository.add(
                    invoice_number=number,
                    customer_id=offer[2],
                    issue_date=today.isoformat(),
                    due_date=due.isoformat(),
                    subtotal=float(offer[6] or 0),
                    discount=float(offer[7] or 0),
                    vat=float(offer[8] or 0),
                    total=float(offer[9] or 0),
                    notes=notes,
                    status="Izdan",
                    vat_liable=offer_repository.get_vat_liable(offer_id),
                )
                break
            except sqlite3.IntegrityError:
                invoice_repository.increase_counter()
        if invoice_id is None:
            raise ValueError("Ni mogoče dodeliti številke računa.")
        invoice_repository.increase_counter()

        for item in items:
            invoice_repository.add_item(
                invoice_id=invoice_id,
                article_id=item[1],
                code=item[2],
                name=item[3],
                description=item[4] or "",
                quantity=item[5],
                unit=item[6],
                price=item[7],
                discount=item[8] or 0,
                vat=item[9],
                total=item[10],
            )

        offer_repository.mark_converted(offer_id, invoice_id)
        return invoice_id, number


offer_service = OfferService()
