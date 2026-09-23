"""Commercial PDF document assembly (invoice / offer / order / delivery)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.pdf.pdf_branding import (
    BANK_ICON_MM,
    CONTENT_WIDTH_MM,
    CUSTOMER_CARD_WIDTH_MM,
    CUSTOMER_ICON_MM,
    FOOTER_BAND_MM,
    FOOTER_RESERVED_MM,
    IDENTITY_TO_TABLE_MM,
    LEFT_MARGIN_MM,
    PAYMENT_COL_WIDTH_MM,
    QR_SIDE_MM,
    RACUN_TOP_INSET_MM,
    RIGHT_MARGIN_MM,
    SIGNATURE_HEIGHT_MM,
    SIGNATURE_ROLE_DEFAULT,
    SIGNATURE_WIDTH_MM,
    TAGLINE,
    TAGLINE_CHAR_SPACE,
    THANKS_BEFORE_MM,
    THANKS_SUBTITLE,
    TOP_MARGIN_MM,
    TOTALS_TO_PAYMENT_GAP_MM,
    VerticalGreenRule,
    SpacedTagline,
    CustomerCard,
    bank_icon,
    customer_people_icon,
    extract_signer_name,
    resolve_palette,
)
from app.pdf.pdf_company import CompanyProfile, existing_path, load_company, load_pdf_options
from app.pdf.pdf_footer import draw_footer
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import image_or_space
from app.pdf.pdf_styles import PAD, ensure_fonts, styles
from app.pdf.pdf_tables import build_items_table, build_summary
from app.pdf.upn_qr import format_reference, format_reference_display
from app.utils.vat import ARTICLE_94_NOTICE, DOCUMENT_FOOTER_MESSAGE, WEBSITE_LABEL, WEBSITE_URL


TITLES = {
    "invoice": "RAČUN",
    "offer": "PONUDBA",
    "order": "NAROČILO",
    "delivery": "DOBAVNICA",
}

# UPN QR side from MASTER image measurement (V15 + 4-module quiet zone = 85 modules).
_QR_MODULE_MM = QR_SIDE_MM / 85.0

# ReportLab Frame adds 6 pt on both horizontal sides. Offset the document
# margins so the actual flowable content lands on the intended 10 mm grid.
_FRAME_SIDE_PADDING_PT = 6.0


class _PagedCanvas(pdf_canvas.Canvas):
    """Two-pass canvas so footer can show ``page / total`` like the MASTER."""

    def __init__(self, *args, website_url: str = "", options: dict | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._website_url = website_url
        self._options = options or {}

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            draw_footer(
                self,
                None,
                self._options.get("footer") or DOCUMENT_FOOTER_MESSAGE,
                website_url=self._website_url,
                options=self._options,
                page_number=self._pageNumber,
                page_count=total,
            )
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)


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


def _due_label(doc_type: str) -> str:
    if doc_type == "invoice":
        return "Rok plačila"
    if doc_type == "order":
        return "Dobava"
    if doc_type == "delivery":
        return "Datum dobave"
    return "Velja do"


class PdfEngine:

    def render(self, document: PdfDocument, output: Path) -> Path:
        company = load_company()
        options = load_pdf_options()
        # Document snapshot overrides display preference for VAT columns.
        if not document.vat_liable:
            options = dict(options)
            options["show_vat"] = False
        output.parent.mkdir(parents=True, exist_ok=True)

        # Reserve only the branded footer band — do not add an extra +4 mm void
        # that pushes thanks onto page 2 for short invoices.
        bottom = max(FOOTER_RESERVED_MM, FOOTER_BAND_MM)
        doc = SimpleDocTemplate(
            str(output),
            pagesize=A4,
            leftMargin=LEFT_MARGIN_MM * mm - _FRAME_SIDE_PADDING_PT,
            rightMargin=RIGHT_MARGIN_MM * mm - _FRAME_SIDE_PADDING_PT,
            topMargin=TOP_MARGIN_MM * mm,
            bottomMargin=bottom * mm,
            title=f"{document.title} {document.number}",
            author=company.name or "JU-TAN Office",
        )
        story = []
        story.extend(build_header(company, options))
        story.extend(self._identity_block(document, options))
        if document.doc_type == "invoice" and document.status == "Storniran":
            look = styles(options)
            story.append(Paragraph("STORNIRANO", look["title"]))
            story.append(Spacer(1, PAD))
        story.append(build_items_table(document.items, options))
        closing = []
        closing.extend(
            build_summary(
                document.subtotal,
                document.discount,
                document.vat,
                document.total,
                options,
                items=document.items,
            )
        )
        if not document.vat_liable:
            look = styles(options)
            closing.append(Spacer(1, 6))
            closing.append(Paragraph(ARTICLE_94_NOTICE, look["art94"]))
        # Totals stay with the table flow. Payment+thanks follow MASTER gap.
        # Keep payment+thanks together so the closing never orphans onto page 2.
        story.extend(closing)

        lower = [Spacer(1, (TOTALS_TO_PAYMENT_GAP_MM - 6.5) * mm)]
        lower.extend(self._payment_block(document, company, options))
        if document.doc_type != "invoice":
            lower.extend(self._signature_block(options))
        lower.extend(self._thanks_block(company, options))
        story.extend(lower)

        if options.get("show_notes") and document.notes:
            look = styles(options)
            story.append(Spacer(1, PAD))
            story.append(Paragraph("Opombe", look["label"]))
            story.append(Paragraph(document.notes.replace("\n", "<br/>"), look["body"]))

        website = options.get("website_url") or company.website or WEBSITE_URL
        if website and not str(website).startswith(("http://", "https://")):
            website = f"http://{website}"

        def _canvas_maker(filename, **kwargs):
            return _PagedCanvas(
                filename,
                website_url=website,
                options=options,
                **kwargs,
            )

        # Footer is drawn by _PagedCanvas (with total page count). Do not also
        # register onFirstPage/onLaterPages or the footer would paint twice.
        doc.build(story, canvasmaker=_canvas_maker)
        return output

    def _identity_block(self, document: PdfDocument, options: dict | None = None):
        """Customer card (left) + document title/meta (right)."""
        options = options or {}
        customer = self._customer_card(document, options)
        title = self._title_meta(document, options)
        gap = 8 * mm
        customer_w = CUSTOMER_CARD_WIDTH_MM * mm
        title_w = CONTENT_WIDTH_MM * mm - customer_w - gap
        row = Table(
            [[customer, Spacer(gap, 1), title]],
            colWidths=[customer_w, gap, title_w],
        )
        row.hAlign = "LEFT"
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        # Hold TABLE_TOP near MASTER after taller customer-card height.
        return [row, Spacer(1, IDENTITY_TO_TABLE_MM * mm)]

    def _title_block(self, document: PdfDocument, options: dict | None = None):
        """Standalone title/meta (kept for unit tests and other callers)."""
        return [self._title_meta(document, options or {}), Spacer(1, PAD)]

    def _title_meta(self, document: PdfDocument, options: dict):
        look = styles(options)
        palette = resolve_palette(options)
        due_label = _due_label(document.doc_type)

        title = Paragraph(document.title, look["title"])
        # MASTER compact unit: RAČUN → short green underline → number beneath.
        accent_w = 18 * mm
        accent = Table([[""]], colWidths=[accent_w], rowHeights=[3.0])
        accent.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), palette["primary"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        number = Paragraph(document.number or "", look["doc_number"])

        meta_rows = [
            [
                Paragraph("Številka:", look["meta_label"]),
                Paragraph(document.number or "—", look["meta_value"]),
            ],
            [
                Paragraph("Datum:", look["meta_label"]),
                Paragraph(document.issue_date or "—", look["meta_value"]),
            ],
            [
                Paragraph(f"{due_label}:", look["meta_label"]),
                Paragraph(document.due_date or "—", look["meta_value"]),
            ],
        ]
        meta = Table(meta_rows, colWidths=[36 * mm, 44 * mm])
        meta.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.35, palette["light_border"]),
                ]
            )
        )

        title_block = Table(
            [
                [title],
                [Spacer(1, 1.2)],
                [accent],
                [Spacer(1, 2.0)],
                [number],
            ],
            colWidths=[64 * mm],
        )
        title_block.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 2), (0, 2), "RIGHT"),
                    ("ALIGN", (0, 4), (0, 4), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        # Right-pack so short underline sits under the left side of RAČUN.
        title_wrap = Table(
            [[Spacer(1, 1), title_block]],
            colWidths=[16 * mm, 64 * mm],
        )
        title_wrap.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        # MASTER RAČUN starts lower than the customer card — inset only the title group.
        stack = Table(
            [
                [Spacer(1, RACUN_TOP_INSET_MM * mm)],
                [title_wrap],
                [Spacer(1, 4.0)],
                [meta],
            ],
            colWidths=[80 * mm],
        )
        stack.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return stack

    def _customer_block(self, document: PdfDocument, options: dict | None = None):
        """Full-width wrapper kept for older callers; render uses the compact card."""
        options = options or {}
        card = self._customer_card(document, options)
        return [card, Spacer(1, PAD)]

    def _customer_card(self, document: PdfDocument, options: dict):
        look = styles(options)
        palette = resolve_palette(options)
        city = document.customer_city or ""

        # MASTER-scale icon tile — thin outline group glyph.
        icon_mm = CUSTOMER_ICON_MM
        icon = customer_people_icon(palette, size=icon_mm * mm)

        from reportlab.lib.styles import ParagraphStyle as _PS

        # Scale type/leading with the taller MASTER card (no empty lower band).
        detail_style = _PS(
            "PdfCustomerBody",
            parent=look["body"],
            leading=19.2,
            fontSize=13.4,
        )
        name_style = _PS(
            "PdfCustomerName",
            parent=look["body_bold"],
            leading=21.0,
            fontSize=16.0,
        )
        kupec_style = _PS(
            "PdfCustomerKupec",
            parent=look["section"],
            fontSize=15.4,
            leading=19.2,
        )

        text_lines = [Paragraph("Kupec", kupec_style)]
        text_lines.append(Spacer(1, 5.4))
        text_lines.append(Paragraph(document.customer_name or "—", name_style))
        text_lines.append(Spacer(1, 3.2))
        if document.customer_address:
            text_lines.append(Paragraph(document.customer_address, detail_style))
        if city:
            text_lines.append(Paragraph(city, detail_style))
        if document.customer_tax:
            text_lines.append(Spacer(1, 3.2))
            text_lines.append(
                Paragraph(f"Davčna št.: {document.customer_tax}", detail_style)
            )

        text_w = CUSTOMER_CARD_WIDTH_MM - icon_mm - 9.0
        text_col = Table([[line] for line in text_lines], colWidths=[text_w * mm])
        text_col.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        inner = Table(
            [[icon, text_col]],
            colWidths=[(icon_mm + 2.0) * mm, (text_w + 3.0) * mm],
        )
        inner.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (1, 0), (1, 0), 4.0),
                ]
            )
        )
        return CustomerCard(inner, CUSTOMER_CARD_WIDTH_MM, palette, radius=4.5)

    def _payment_block(self, document: PdfDocument, company: CompanyProfile, options: dict):
        if document.doc_type in ("order", "delivery") or document.status == "Storniran":
            return []
        look = styles(options)
        palette = resolve_palette(options)
        method = document.payment_method or options.get("payment_method") or "Nakazilo"
        due_label = _due_label(document.doc_type)

        heading = Table(
            [
                [
                    bank_icon(palette, size=BANK_ICON_MM * mm),
                    Paragraph("Podatki za plačilo", look["section"]),
                ]
            ],
            colWidths=[(BANK_ICON_MM + 3) * mm, 58 * mm],
        )
        heading.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 4.0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        detail_rows = []
        if document.doc_type != "invoice":
            detail_rows.append(
                [Paragraph("Način plačila:", look["meta_label"]), Paragraph(method, look["body"])]
            )

        iban_text = company.iban or "—"
        bank = (getattr(company, "bank", "") or "").strip()
        if company.iban and bank:
            iban_text = f"{company.iban} ({bank})"
        detail_rows.append(
            [Paragraph("TRR:", look["meta_label"]), Paragraph(iban_text, look["body"])]
        )

        if document.doc_type != "invoice":
            detail_rows.append(
                [
                    Paragraph(f"{due_label}:", look["meta_label"]),
                    Paragraph(document.due_date or "—", look["body"]),
                ]
            )
        if document.doc_type == "invoice":
            sklic_raw = (document.reference or "").strip() or format_reference(document.number)
            sklic = format_reference_display(sklic_raw)
            detail_rows.append(
                [Paragraph("Sklic:", look["meta_label"]), Paragraph(sklic, look["body"])]
            )
            detail_rows.append(
                [
                    Paragraph("Namen:", look["meta_label"]),
                    Paragraph(f"Plačilo računa št. {document.number}", look["body"]),
                ]
            )

        # Keep the nested payment table inside PAYMENT_COL_WIDTH_MM exactly.
        # The wider value column keeps IBAN + bank on one line on Linux too.
        details = Table(detail_rows, colWidths=[12 * mm, 68 * mm])
        details.setStyle(
            TableStyle(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        pay_w = PAYMENT_COL_WIDTH_MM * mm
        pay_col = Table(
            [[heading], [Spacer(1, 3.0)], [details]],
            colWidths=[pay_w],
        )
        pay_col.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        qr = self._qr_flowable(document, company, options, module_mm=_QR_MODULE_MM)
        # Production invoices: PAYMENT | QR only. Never signature/stamp/placeholder.
        # Do NOT call _inline_signature here — that path draws Tanja Hrup / Direktorica.

        rule_w = 1.6 * mm
        qr_w = (QR_SIDE_MM + 4) * mm

        cells = [pay_col]
        widths = [pay_w]
        if qr is not None:
            rule = VerticalGreenRule(QR_SIDE_MM + 1, palette)
            residual = max(CONTENT_WIDTH_MM * mm - pay_w - rule_w - qr_w, 0)
            cells.extend([rule, qr])
            widths.extend([rule_w, qr_w])
            if residual > 0.5 * mm:
                cells.append(Spacer(residual, 1))
                widths.append(residual)

        if len(cells) == 1:
            content = pay_col
        else:
            style_cmds = [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
            if qr is not None:
                style_cmds.append(("ALIGN", (2, 0), (2, 0), "CENTER"))
            content = Table([cells], colWidths=widths)
            content.setStyle(TableStyle(style_cmds))

        # Keep the payment area clean and unobstructed.
        return [Spacer(1, 1), content]

    def _qr_flowable(
        self,
        document: PdfDocument,
        company: CompanyProfile,
        options: dict | None = None,
        *,
        module_mm: float = _QR_MODULE_MM,
    ):
        if document.doc_type != "invoice":
            return None
        import segno

        from app.pdf.upn_qr import build_upn_qr

        city = " ".join(
            part for part in (company.postal_code or "", company.city or "") if part
        ).strip()
        reference = (document.reference or "").strip() or format_reference(document.number)
        # Fall back to a standards-compliant SI00 reference when the stored
        # value is not a valid UPN reference (e.g. "SI00 RAC-0002").
        payload = build_upn_qr(
            iban=company.iban or "",
            recipient_name=company.name or "",
            recipient_address=company.address or "",
            recipient_city=city,
            amount=document.total,
            reference=reference,
            purpose=f"Plačilo računa št. {document.number}",
            due_date=document.due_date or "",
            payer_name=document.customer_name or "",
            payer_address=document.customer_address or "",
            payer_city=document.customer_city or "",
        )
        if not payload:
            payload = build_upn_qr(
                iban=company.iban or "",
                recipient_name=company.name or "",
                recipient_address=company.address or "",
                recipient_city=city,
                amount=document.total,
                reference=format_reference(document.number),
                purpose=f"Plačilo računa št. {document.number}",
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
        module = float(module_mm) * mm
        border = 4
        matrix = tuple(code.matrix)
        modules = len(matrix)
        size = (modules + 2 * border) * module
        drawing = Drawing(size, size)
        from reportlab.lib.colors import black, white

        # UPN QR must have an opaque white background and a clean 4-module
        # quiet zone. The payment watermark must never show through the code.
        drawing.add(
            Rect(
                0,
                0,
                size,
                size,
                strokeWidth=0,
                fillColor=white,
            )
        )

        for y, row in enumerate(matrix):
            for x, dark in enumerate(row):
                if dark:
                    drawing.add(
                        Rect(
                            (x + border) * module,
                            (modules - 1 - y + border) * module,
                            module,
                            module,
                            strokeWidth=0,
                            fillColor=black,
                        )
                    )
        label = Paragraph("Plačilo z UPN QR", look["caption"])
        qr_box = Table([[drawing], [Spacer(1, 2)], [label]], colWidths=[size])
        qr_box.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return qr_box

    def _inline_signature(self, options: dict, company: CompanyProfile | None = None):
        """Legacy helper for non-invoice docs only — NEVER call from invoice payment.

        Draws green line + signer name (e.g. Tanja Hrup) + role (Direktorica).
        """
        look = styles(options)
        palette = resolve_palette(options)
        sign_path = existing_path(options.get("signature_path", ""))
        sig_w = SIGNATURE_WIDTH_MM
        sig_h = SIGNATURE_HEIGHT_MM
        if sign_path:
            graphic = image_or_space(sign_path, sig_w, sig_h)
        else:
            graphic = Spacer(sig_w * mm, sig_h * mm)

        line = Table([[""]], colWidths=[sig_w * mm], rowHeights=[3.5])
        line.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 0.85, palette["primary"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        signer = ""
        if company is not None:
            signer = extract_signer_name(company.name or "")
        name_para = Paragraph(signer or " ", look["sign_name"]) if signer else Paragraph(" ", look["caption"])
        role_para = Paragraph(SIGNATURE_ROLE_DEFAULT if signer else "Podpis", look["sign_role"])

        rows = [[graphic], [line], [Spacer(1, 1.5)], [name_para], [role_para]]
        block = Table(rows, colWidths=[(sig_w + 2) * mm])
        block.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (0, 0), "BOTTOM"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
                ]
            )
        )
        return block

    def _thanks_block(self, company: CompanyProfile, options: dict):
        look = styles(options)
        palette = resolve_palette(options)
        regular, _bold = ensure_fonts()
        # Approved reference closing line (configured footer remains elsewhere).
        sub = THANKS_SUBTITLE

        thanks_accent = Table([[""]], colWidths=[28 * mm], rowHeights=[3.0])
        thanks_accent.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), palette["primary"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        left = Table(
            [
                [Paragraph("Hvala za zaupanje!", look["thanks"])],
                [thanks_accent],
                [Spacer(1, 2.6)],
                [Paragraph(sub, look["thanks_sub"])],
            ],
            colWidths=[112 * mm],
        )
        left.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
                    ("ALIGN", (0, 1), (0, 1), "LEFT"),
                ]
            )
        )

        website = (company.website or options.get("website_url") or WEBSITE_URL or "").strip()
        display = website.replace("https://", "").replace("http://", "") or WEBSITE_LABEL
        tag = SpacedTagline(
            TAGLINE,
            78 * mm,
            font_name=regular,
            font_size=9.2,
            color=palette["muted"],
            char_space=TAGLINE_CHAR_SPACE * 0.85,
            align="right",
        )
        right = Table(
            [
                [tag],
                [Spacer(1, 1.2)],
                [Paragraph(display, look["brand_web"])],
            ],
            colWidths=[78 * mm],
        )
        right.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
                ]
            )
        )

        row = Table(
            [[left, right]],
            colWidths=[114 * mm, 78 * mm],
        )
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        # Explicit MASTER thanks landmark (do not collapse under payment).
        return [Spacer(1, THANKS_BEFORE_MM * mm), row]

    def _signature_block(self, options: dict):
        """Signature/stamp only when enabled. OFF => zero Flowables (no labels/spacers).

        Used by non-invoice documents. Invoice stamps are never rendered.
        """
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
                TableStyle(
                    [
                        ("LINEBELOW", (0, 0), (-1, -1), 0.7, palette["muted"]),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
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
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("BACKGROUND", (0, 0), (-1, -1), palette["surface"]),
                        ("BOX", (0, 0), (-1, -1), 0.4, palette["border"]),
                    ]
                )
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
