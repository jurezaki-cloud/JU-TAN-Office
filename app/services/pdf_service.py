from app.pdf.pdf_export import pdf_export


class PDFService:
    """Ovoj za enoten Enterprise PDF Engine."""

    def generate(self, invoice):
        invoice_id = getattr(invoice, "id", invoice)
        return pdf_export.export_invoice(invoice_id)

    def generate_async(self, invoice, on_done, on_error=None):
        from app.core.jobs import run_in_thread

        invoice_id = getattr(invoice, "id", invoice)
        return run_in_thread(
            lambda: pdf_export.export_invoice(invoice_id),
            on_done=on_done,
            on_error=on_error,
        )


pdf_service = PDFService()
