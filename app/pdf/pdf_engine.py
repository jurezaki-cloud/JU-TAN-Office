from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.pdf.pdf_company import CompanyProfile, existing_path, load_company, load_pdf_options
from app.pdf.pdf_footer import draw_footer
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import image_or_space
from app.pdf.pdf_styles import BORDER, PAD, MUTED, styles
from app.pdf.pdf_tables import build_items_table, build_summary
from app.utils.vat import ARTICLE_94_NOTICE, DOCUMENT_FOOTER_MESSAGE, WEBSITE_URL


TITLES = {
    "invoice": "RAČUN",
    "offer": "PONUDBA",
    "order": "NAROČILO",
    "delivery": "DOBAVNICA",
}


@dataclass
class PdfDocument:
    doc_type: str
    number: str
    issue_date: str = ""
    due_date: str = ""
    reference: str = ""
    payment_method: str = ""
    notes: str = ""
    customer_name: str = ""
    customer_address: str = ""
    customer_city: str = ""
    customer_tax: str = ""
    items: list[dict] = field(default_factory=list)
    subtotal: float = 0
    discount: float = 0
    vat: float = 0
    total: float = 0
    status: str = ""
    vat_liable: bool = True

    @property
    def title(self) -> str:
        return TITLES.get(self.doc_type, self.doc_type.upper())


class PdfEngine:

    def render(self, document: PdfDocument, output: Path) -> Path:
        company = load_company()
        options = load_pdf_options()
        # Document snapshot overrides display preference for VAT columns.
        if not document.vat_liable:
            options = dict(options)
            options["show_vat"] = False
        output.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=16 * mm,
            bottomMargin=28 * mm,
            title=f"{document.title} {document.number}",
            author=company.name or "JU-TAN Office",
        )
        story = []
        story.extend(build_header(company, options))
        story.extend(self._title_block(document))
        if document.doc_type == "invoice" and document.status == "Storniran":
            look = styles()
            story.append(Paragraph("STORNIRANO", look["title"]))
            story.append(Spacer(1, PAD))
        story.extend(self._customer_block(document))
        story.append(build_items_table(document.items, options))
        story.extend(
            build_summary(
                document.subtotal,
                document.discount,
                document.vat,
                document.total,
                options,
            )
        )
        if not document.vat_liable:
            look = styles()
            story.append(Spacer(1, PAD))
            story.append(Paragraph(ARTICLE_94_NOTICE, look["body"]))
        story.extend(self._payment_block(document, company, options))
        if options.get("show_notes") and document.notes:
            look = styles()
            story.append(Spacer(1, PAD))
            story.append(Paragraph("Opombe", look["label"]))
            story.append(Paragraph(document.notes.replace("\n", "<br/>"), look["body"]))
        story.extend(self._signature_block(options))

        footer_text = options.get("footer") or DOCUMENT_FOOTER_MESSAGE
        website = options.get("website_url") or company.website or WEBSITE_URL
        if website and not str(website).startswith(("http://", "https://")):
            website = f"http://{website}"
        doc.build(
            story,
            onFirstPage=lambda c, d: draw_footer(c, d, footer_text, website_url=website),
            onLaterPages=lambda c, d: draw_footer(c, d, footer_text, website_url=website),
        )
        return output

    def _title_block(self, document: PdfDocument):
        look = styles()
        due_label = "Rok plačila" if document.doc_type == "invoice" else "Velja do"
        if document.doc_type == "order":
            due_label = "Dobava"
        if document.doc_type == "delivery":
            due_label = "Datum dobave"
        meta = Table(
            [
                [Paragraph("Številka", look["label"]), Paragraph(document.number, look["body"])],
                [Paragraph("Datum", look["label"]), Paragraph(document.issue_date or "—", look["body"])],
                [Paragraph(due_label, look["label"]), Paragraph(document.due_date or "—", look["body"])],
            ],
            colWidths=[32 * mm, 50 * mm],
        )
        meta.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        row = Table(
            [[Paragraph(document.title, look["title"]), meta]],
            colWidths=[98 * mm, 82 * mm],
        )
        row.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        return [row, Spacer(1, PAD)]

    def _customer_block(self, document: PdfDocument):
        look = styles()
        city = document.customer_city or ""
        block = [
            Paragraph("Kupec", look["label"]),
            Paragraph(document.customer_name or "—", look["body"]),
            Paragraph(document.customer_address or "", look["body"]),
            Paragraph(city, look["body"]),
        ]
        if document.customer_tax:
            block.append(Paragraph(f"Davčna: {document.customer_tax}", look["body"]))
        return block + [Spacer(1, PAD)]

    def _payment_block(self, document: PdfDocument, company: CompanyProfile, options: dict):
        if document.doc_type in ("order", "delivery") or document.status == "Storniran":
            return []
        look = styles()
        method = document.payment_method or options.get("payment_method") or "Nakazilo"
        due_label = "Rok plačila" if document.doc_type == "invoice" else "Velja do"
        data = [
            [Paragraph("Način plačila", look["label"]), Paragraph(method, look["body"])],
            [Paragraph("TRR", look["label"]), Paragraph(company.iban or "—", look["body"])],
            [Paragraph(due_label, look["label"]), Paragraph(document.due_date or "—", look["body"])],
        ]
        # Payment reference (sklic) is invoice-specific; keep commercial TRR/method on offers.
        if document.doc_type == "invoice":
            data.append(
                [Paragraph("Sklic", look["label"]), Paragraph(document.reference or document.number, look["body"])],
            )
        table = Table(data, colWidths=[40 * mm, 140 * mm])
        table.setStyle(
            TableStyle([
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LINEABOVE", (0, 0), (-1, 0), 0.4, BORDER),
            ])
        )
        blocks = [Spacer(1, PAD), table]
        # Slightly denser QR when signature/stamp also consume vertical space,
        # so a short invoice + UPN + signing lines still fit on one A4 page.
        compact = bool(options.get("show_signature") or options.get("show_stamp"))
        qr = self._qr_flowable(document, company, module_mm=0.52 if compact else 0.65)
        if qr is not None:
            blocks.append(Spacer(1, PAD))
            blocks.append(qr)
        return blocks

    def _qr_flowable(self, document: PdfDocument, company: CompanyProfile, *, module_mm: float = 0.65):
        if document.doc_type != "invoice":
            return None
        import segno
        from reportlab.graphics.shapes import Drawing, Rect
        from reportlab.platypus import KeepTogether

        from app.pdf.upn_qr import build_upn_qr

        city = " ".join(
            part for part in (company.postal_code or "", company.city or "") if part
        ).strip()
        payload = build_upn_qr(
            iban=company.iban or "",
            recipient_name=company.name or "",
            recipient_address=company.address or "",
            recipient_city=city,
            amount=document.total,
            reference=document.reference or document.number,
            purpose=f"Račun {document.number}",
            due_date=document.due_date or "",
            payer_name=document.customer_name or "",
            payer_address=document.customer_address or "",
            payer_city=document.customer_city or "",
        )
        if not payload:
            return None

        look = styles()
        code = segno.make(
            payload,
            version=15,
            error="m",
            mode="byte",
            encoding="iso-8859-2",
            eci=True,
            micro=False,
            boost_error=False,
        )
        # ZBS: V15 = 77x77 modules, module ~0.4–0.65 mm, 4-module quiet zone.
        module = float(module_mm) * mm
        border = 4
        matrix = tuple(code.matrix)
        modules = len(matrix)
        size = (modules + 2 * border) * module
        drawing = Drawing(size, size)
        for y, row in enumerate(matrix):
            for x, dark in enumerate(row):
                if dark:
                    drawing.add(Rect(
                        (x + border) * module,
                        (modules - 1 - y + border) * module,
                        module,
                        module,
                        strokeWidth=0,
                        fillColor=None,
                    ))
        # Rect defaults are not safe for barcode output; force solid black modules.
        from reportlab.lib.colors import black
        for shape in drawing.contents:
            shape.fillColor = black
        label = Paragraph("UPN QR za plačilo", look["label"])
        return KeepTogether([label, drawing])

    def _signature_block(self, options: dict):
        """Signature/stamp only when enabled. OFF => zero Flowables (no labels/spacers)."""
        show_stamp = bool(options.get("show_stamp"))
        show_sign = bool(options.get("show_signature"))
        if not show_stamp and not show_sign:
            return []

        look = styles()
        stamp_path = existing_path(options.get("stamp_path", ""))
        sign_path = existing_path(options.get("signature_path", ""))

        def _signing_line(width_mm: float = 40):
            # Compact ink line — never reserve a tall empty image box (forced page 2).
            line = Table([[""]], colWidths=[width_mm * mm], rowHeights=[6])
            line.setStyle(
                TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.7, MUTED),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            return line

        def _slot(enabled: bool, path: str, caption: str):
            if not enabled:
                return []
            if path:
                graphic = image_or_space(path, 36, 14)
            else:
                graphic = _signing_line(36)
            return [graphic, Paragraph(caption, look["caption"])]

        left = _slot(show_stamp, stamp_path, "Žig")
        right = _slot(show_sign, sign_path, "Podpis")
        if show_stamp and show_sign:
            row = [[left, right]]
            widths = [90 * mm, 90 * mm]
        elif show_stamp:
            row = [[left]]
            widths = [180 * mm]
        else:
            row = [[right]]
            widths = [180 * mm]

        table = Table(row, colWidths=widths)
        style_cmds = [
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("TEXTCOLOR", (0, 0), (-1, -1), MUTED),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
        if show_stamp and show_sign:
            style_cmds += [
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        elif show_sign:
            style_cmds.append(("ALIGN", (0, 0), (0, 0), "RIGHT"))
        else:
            style_cmds.append(("ALIGN", (0, 0), (0, 0), "LEFT"))
        table.setStyle(TableStyle(style_cmds))
        return [Spacer(1, 6), table]


pdf_engine = PdfEngine()
