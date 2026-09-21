from app.database.offer_repository import offer_repository


class NumberingService:

    def next_offer_number(self):
        """Peek next offer number for UI preview (does not reserve)."""
        return offer_repository.get_next_number()


numbering_service = NumberingService()
