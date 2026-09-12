from app.database.invoice_repository import invoice_repository


class InvoiceService:

    def get_all(self):
        return invoice_repository.get_all()

    def get_by_id(self, invoice_id):
        return invoice_repository.get_by_id(invoice_id)

    def search(self, text):
        return invoice_repository.search(text)

    def get_next_number(self):
        return invoice_repository.get_next_number()

    def increase_counter(self):
        return invoice_repository.increase_counter()

    def add(
        self,
        invoice_number,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        notes,
    ):
        return invoice_repository.add(
            invoice_number,
            customer_id,
            issue_date,
            due_date,
            subtotal,
            discount,
            vat,
            total,
            notes,
        )

    def update(
        self,
        invoice_id,
        customer_id,
        issue_date,
        due_date,
        subtotal,
        discount,
        vat,
        total,
        status,
        notes,
    ):
        return invoice_repository.update(
            invoice_id,
            customer_id,
            issue_date,
            due_date,
            subtotal,
            discount,
            vat,
            total,
            status,
            notes,
        )

    def delete(self, invoice_id):
        return invoice_repository.delete(invoice_id)

    def duplicate(self, invoice_id):
        return invoice_repository.duplicate(invoice_id)


invoice_service = InvoiceService()