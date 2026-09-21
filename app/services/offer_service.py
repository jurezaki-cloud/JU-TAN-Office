"""Offer business rules (conversion, edit protection)."""

from __future__ import annotations

from datetime import date, timedelta

from app.database.database import db
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

        The full conversion (number allocation, invoice, items, offer lock)
        runs in a single BEGIN IMMEDIATE transaction.
        """
        offer = offer_repository.get_by_id(offer_id)
        if offer is None:
            raise ValueError("Ponudba ne obstaja.")

        items = offer_repository.get_items(offer_id)
        if not items:
            raise ValueError("Ponudba nima postavk.")

        today = date.today()
        due = today + timedelta(days=30)
        notes = (offer[10] or "") + (f"\n[Iz ponudbe {offer[1]}]" if offer[1] else "")
        vat_liable = offer_repository.get_vat_liable(offer_id)

        # Schema upgrades commit; run them before the conversion transaction.
        offer_repository.ensure_schema()
        invoice_repository.ensure_schema()

        with db.transaction(immediate=True) as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT converted_invoice_id FROM offers WHERE id=?",
                (offer_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Ponudba ne obstaja.")
            if row[0] is not None:
                raise ValueError(
                    "Ponudba je že pretvorjena v račun. Ponovna pretvorba ni dovoljena."
                )

            number = invoice_repository.allocate_next_number(conn)
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
                vat_liable=vat_liable,
                conn=conn,
            )

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
                    conn=conn,
                )

            offer_repository.mark_converted(offer_id, invoice_id, conn=conn)

        return invoice_id, number


offer_service = OfferService()
