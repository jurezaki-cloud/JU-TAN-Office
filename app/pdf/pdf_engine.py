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

from app.pdf.pdf_branding import resolve_palette
from app.pdf.pdf_company import CompanyProfile, existing_path, load_company, load_pdf_options
from app.pdf.pdf_footer import draw_footer
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import image_or_space
from app.pdf.pdf_styles import PAD, styles
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
            topMargin=14 * mm,
            bottomMargin=28 * mm,
            title=f"{document.title} {document.number}",
            author=company.name or "JU-TAN Office",
        )
        story = []
        story.extend(build_header(company, options))
        story.extend(self._title_block(document, options))
        if document.doc_type == "invoice" and document.status == "Storniran":
            look = styles(options)
            story.append(Paragraph("STORNIRANO", look["title"]))
            story.append(Spacer(1, PAD))
        story.extend(self._customer_block(document, options))
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
            look = styles(options)
            story.append(Spacer(1, PAD))
            story.append(Paragraph(ARTICLE_94_NOTICE, look["body"]))
        story.extend(self._payment_block(document, company, options))
        if options.get("show_notes") and document.notes:
            look = styles(options)
            story.append(Spacer(1, PAD))
            story.append(Paragraph("Opombe", look["label"]))
            story.append(Paragraph(document.notes.replace("\n", "<br/>"), look["body"]))
        story.extend(self._signature_block(options))

        footer_text = options.get("footer") or DOCUMENT_FOOTER_MESSAGE
        website = options.get("website_url") or company.website or WEBSITE_URL
        if website and not str(website).startswith(("http://", "https://")):
            website = f"http://{website}"

        def _footer(canvas, d):
            draw_footer(
                canvas,
                d,
                footer_text,
                website_url=website,
                options=options,
            )

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return output

    def _title_block(self, document: PdfDocument, options: dict | None = None):
        options = options or {}
        look = styles(options)
        palette = resolve_palette(options)
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
                ("BACKGROUND", (0, 0), (-1, -1), palette["table_header"]),
                ("BOX", (0, 0), (-1, -1), 0.35, palette["border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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

    def _customer_block(self, document: PdfDocument, options: dict | None = None):
        options = options or {}
        look = styles(options)
        palette = resolve_palette(options)
        city = document.customer_city or ""
        lines = [
            Paragraph("Kupec", look["label"]),
            Paragraph(document.customer_name or "—", look["body"]),
            Paragraph(document.customer_address or "", look["body"]),
            Paragraph(city, look["body"]),
        ]
        if document.customer_tax:
            lines.append(Paragraph(f"Davčna: {document.customer_tax}", look["body"]))
        panel = Table([[lines]], colWidths=[180 * mm])
        panel.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), palette["table_header"]),
                ("BOX", (0, 0), (-1, -1), 0.35, palette["border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBEFORE", (0, 0), (0, 0), 2.5, palette["primary"]),
            ])
        )
        return [panel, Spacer(1, PAD)]

    def _payment_block(self, document: PdfDocument, company: CompanyProfile, options: dict):
        if document.doc_type in ("order", "delivery") or document.status == "Storniran":
            return []
        look = styles(options)
        palette = resolve_palette(options)
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
        details = Table(data, colWidths=[36 * mm, 74 * mm])
        details.setStyle(
            TableStyle([
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        compact = bool(options.get("show_signature") or options.get("show_stamp"))
        qr = self._qr_flowable(document, company, options, module_mm=0.52 if compact else 0.65)

        heading = Paragraph("Plačilni podatki", look["label"])
        if qr is not None:
            inner = Table(
                [[details, qr]],
                colWidths=[112 * mm, 60 * mm],
            )
            inner.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ("LEFTPADDING", (1, 0), (1, 0), 4),
                ])
            )
            content = [[heading], [inner]]
        else:
            content = [[heading], [details]]

        panel = Table(content, colWidths=[180 * mm])
        panel.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), palette["surface"]),
                ("BOX", (0, 0), (-1, -1), 0.45, palette["border"]),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, palette["primary"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        return [Spacer(1, PAD), panel]

    def _qr_flowable(
        self,
        document: PdfDocument,
        company: CompanyProfile,
        options: dict | None = None,
        *,
        module_mm: float = 0.65,
    ):
        if document.doc_type != "invoice":
            return None
        import segno
        from reportlab.graphics.shapes import Drawing, Rect

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

        look = styles(options)
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
        from reportlab.lib.colors import black
        for shape in drawing.contents:
            shape.fillColor = black
        label = Paragraph("UPN QR za plačilo", look["label"])
        # KeepTogether inside a Table reports an effectively infinite height to
        # ReportLab (0xFFFFFF), which made invoice/offer PDF export fail.
        qr_box = Table([[label], [drawing]], colWidths=[size])
        qr_box.setStyle(
            TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        return qr_box

    def _signature_block(self, options: dict):
        """Signature/stamp only when enabled. OFF => zero Flowables (no labels/spacers)."""
        show_stamp = bool(options.get("show_stamp"))
        show_sign = bool(options.get("show_signature"))
        if not show_stamp and not show_sign:
            return []

        look = styles(options)
        palette = resolve_palette(options)
        stamp_path = existing_path(options.get("stamp_path", ""))
        sign_path = existing_path(options.get("signature_path", ""))

        def _signing_line(width_mm: float = 40):
            line = Table([[""]], colWidths=[width_mm * mm], rowHeights=[6])
            line.setStyle(
                TableStyle([
                    ("LINEBELOW", (0, 0), (-1, -1), 0.7, palette["muted"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            return line

        def _slot(enabled: bool, path: str, caption: str):
            if not enabled:
                return None
            if path:
                graphic = image_or_space(path, 36, 14)
            else:
                graphic = _signing_line(36)
            inner = Table(
                [[graphic], [Paragraph(caption, look["caption"])]],
                colWidths=[70 * mm],
            )
            inner.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("BACKGROUND", (0, 0), (-1, -1), palette["surface"]),
                    ("BOX", (0, 0), (-1, -1), 0.4, palette["border"]),
                ])
            )
            return inner

        left = _slot(show_stamp, stamp_path, "Žig")
        right = _slot(show_sign, sign_path, "Podpis")
        cells = []
        widths = []
        if left is not None:
            cells.append(left)
            widths.append(90 * mm)
        if right is not None:
            cells.append(right)
            widths.append(90 * mm)

        table = Table([cells], colWidths=widths)
        style_cmds = [
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
        if len(cells) == 2:
            style_cmds += [
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        elif show_sign:
            style_cmds.append(("ALIGN", (0, 0), (0, 0), "RIGHT"))
        else:
            style_cmds.append(("ALIGN", (0, 0), (0, 0), "LEFT"))
        table.setStyle(TableStyle(style_cmds))
        return [Spacer(1, 8), table]


pdf_engine = PdfEngine()
