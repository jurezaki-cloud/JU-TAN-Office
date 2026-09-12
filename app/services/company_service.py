from app.database.company_repository import company_repository


class CompanyService:

    def load(self):
        return company_repository.get()

    def save(
        self,
        name,
        legal_name,
        address,
        postal_code,
        city,
        country,
        tax_number,
        registration_number,
        iban,
        bank,
        email,
        website,
        phone,
        mobile,
        logo,
        invoice_prefix,
        offer_prefix,
        invoice_counter,
        offer_counter,
        default_vat,
        notes,
    ):

        company_repository.save(
            name,
            legal_name,
            address,
            postal_code,
            city,
            country,
            tax_number,
            registration_number,
            iban,
            bank,
            email,
            website,
            phone,
            mobile,
            logo,
            invoice_prefix,
            offer_prefix,
            invoice_counter,
            offer_counter,
            default_vat,
            notes,
        )


company_service = CompanyService()