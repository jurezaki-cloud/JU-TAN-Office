from app.database.customer_repository import customer_repository


class CustomerService:

    def get_all(self):
        return customer_repository.get_all()

    def get_by_id(self, customer_id):
        return customer_repository.get_by_id(customer_id)

    def search(self, text):
        return customer_repository.search(text)

    def add(
        self,
        company,
        contact,
        address,
        postal_code,
        city,
        country,
        tax_number,
        email,
        phone,
    ):
        return customer_repository.add(
            company,
            contact,
            address,
            postal_code,
            city,
            country,
            tax_number,
            email,
            phone,
        )

    def delete(self, customer_id):
        return customer_repository.delete(customer_id)


customer_service = CustomerService()