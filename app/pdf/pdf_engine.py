"""Commercial PDF document assembly (invoice / offer / order / delivery)."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from app.core.date_format import format_date

from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    Image,
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
    PAYMENT_TO_TOTALS_GUTTER_MM,
    QR_SIDE_MM,
    RACUN_TOP_INSET_MM,
    RIGHT_MARGIN_MM,
    SIGNATURE_HEIGHT_MM,
    SIGNATURE_WIDTH_MM,
    TAGLINE,
    TAGLINE_CHAR_SPACE,
    THANKS_BEFORE_MM,
    THANKS_SUBTITLE,
    TOP_MARGIN_MM,
    TOTAL_BAR_HEIGHT_MM,
    TOTAL_BAR_WIDTH_MM,
    TOTALS_TO_CLOSING_MM,
    TOTALS_TO_SIGNATURE_MM,
    TOTALS_WIDTH_MM,
    VerticalGreenRule,
    SpacedTagline,
    CustomerCard,
    bank_icon,
    customer_people_icon,
    resolve_palette,
    resolve_signer_name,
)
from app.pdf.pdf_company import CompanyProfile, existing_path, load_company, load_pdf_options
from app.pdf.pdf_footer import BrandFooterBand, NOTES_TO_FOOTER_MM, draw_footer
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import image_or_space, resolve_pdf_logo_path
from app.pdf.pdf_styles import PAD, ensure_fonts, styles
from app.pdf.pdf_tables import build_items_table, build_summary, build_totals_stack
from app.pdf.pdf_text import NBSP, esc, format_iban
from app.pdf.upn_qr import format_reference, format_reference_display
from app.utils.flags import parse_bool
from app.utils.vat import ARTICLE_94_NOTICE, DOCUMENT_FOOTER_MESSAGE, WEBSITE_LABEL, WEBSITE_URL


TITLES = {
    "invoice": "RAČUN",
    "offer": "PONUDBA",
    "proforma": "PREDRAČUN",
    "order": "NAROČILO",
    "delivery": "DOBAVNICA",
}

# UPN QR side from MASTER image measurement (V15 + 4-module quiet zone = 85 modules).
_QR_MODULE_MM = QR_SIDE_MM / 85.0

# ReportLab Frame adds 6 pt on both horizontal sides. Offset the document
# margins so the actual flowable content lands on the intended 10 mm grid.
_FRAME_SIDE_PADDING_PT = 6.0

_NO_PADDING = (
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
)


class _PagedCanvas(pdf_canvas.Canvas):
    """Two-pass canvas so footer can show ``page / total`` like the MASTER."""

    def __init__(
        self,
        *args,
        website_url: str = "",
        options: dict | None = None,
        logo_path: str = "",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._website_url = website_url
        self._options = options or {}
        self._logo_path = logo_path

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
                logo_path=self._logo_path,
                draw_brand=False,
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
    if doc_type in {"invoice", "proforma"}:
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
        if self._has_payment(document):
            story.extend(self._closing_section(document, company, options))
        else:
            story.extend(
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
                story.append(Spacer(1, 6))
                story.append(Paragraph(ARTICLE_94_NOTICE, look["art94"]))
            story.append(Spacer(1, TOTALS_TO_CLOSING_MM * mm))
            if document.doc_type not in ("invoice", "offer"):
                story.extend(self._signature_block(options))
        # Brand footer composition follows closing content (not page-bottom
        # anchored) so short invoices do not leave a large white hole.
        if options.get("show_notes") and document.notes:
            look = styles(options)
            story.append(Spacer(1, 2.5 * mm))
            notes_box = Table(
                [[Paragraph("Opombe", look["label"])],
                 [Paragraph(esc(document.notes).replace("\n", "<br/>"), look["body"])]],
                colWidths=[CONTENT_WIDTH_MM * mm],
            )
            notes_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), resolve_palette(options)["light_green"]),
                ("BOX", (0, 0), (-1, -1), 0.45, resolve_palette(options)["light_border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(notes_box)

        website = options.get("website_url") or company.website or WEBSITE_URL
        if website and not str(website).startswith(("http://", "https://")):
            website = f"http://{website}"

        story.append(Spacer(1, NOTES_TO_FOOTER_MM * mm))
        story.append(
            BrandFooterBand(
                website_url=website,
                options=options,
                width_mm=CONTENT_WIDTH_MM,
            )
        )

        # Header logo resolution (footer brand band no longer uses the logo).
        logo_path = ""
        if parse_bool(options.get("show_logo"), default=True):
            resolved_logo = resolve_pdf_logo_path(getattr(company, "logo", "") or "")
            logo_path = str(resolved_logo) if resolved_logo else ""

        def _canvas_maker(filename, **kwargs):
            return _PagedCanvas(
                filename,
                website_url=website,
                options=options,
                logo_path=logo_path,
                **kwargs,
            )

        # Page label is drawn by _PagedCanvas. Brand composition is in the story.
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
        number = Paragraph(esc(document.number), look["doc_number"])

        meta_rows = [
            [
                Paragraph("Številka:", look["meta_label"]),
                Paragraph(esc(document.number or "—"), look["meta_value"]),
            ],
            [
                Paragraph("Datum:", look["meta_label"]),
                Paragraph(esc(format_date(document.issue_date)), look["meta_value"]),
            ],
            [
                Paragraph(f"{due_label}:", look["meta_label"]),
                Paragraph(esc(format_date(document.due_date)), look["meta_value"]),
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

        # Compact DL-window typography: the postal name and address remain
        # inside the first 99 mm fold panel without sacrificing hierarchy.
        detail_style = _PS(
            "PdfCustomerBody",
            parent=look["body"],
            leading=14.2,
            fontSize=10.8,
        )
        name_style = _PS(
            "PdfCustomerName",
            parent=look["body_bold"],
            leading=15.8,
            fontSize=12.6,
        )
        kupec_style = _PS(
            "PdfCustomerKupec",
            parent=look["section"],
            fontSize=11.4,
            leading=14.0,
        )

        text_lines = [Paragraph("Kupec", kupec_style)]
        text_lines.append(Spacer(1, 1.8))
        text_lines.append(Paragraph(esc(document.customer_name or "—"), name_style))
        text_lines.append(Spacer(1, 1.0))
        if document.customer_address:
            text_lines.append(Paragraph(esc(document.customer_address), detail_style))
        if city:
            text_lines.append(Paragraph(esc(city), detail_style))
        if document.customer_tax:
            text_lines.append(Spacer(1, 1.0))
            text_lines.append(
                Paragraph(f"Davčna št.: {esc(document.customer_tax)}", detail_style)
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

    @staticmethod
    def _has_payment(document: PdfDocument) -> bool:
        return document.doc_type in ("invoice", "offer") and document.status != "Storniran"

    def _closing_section(self, document: PdfDocument, company: CompanyProfile, options: dict):
        """MASTER closing: right-aligned totals, full-width pay rail, then 3 cards."""
        look = styles(options)
        stack, _bar_top = build_totals_stack(
            document.subtotal,
            document.discount,
            document.vat,
            document.total,
            options,
            items=document.items,
        )

        payment_parts = self._payment_block(document, company, options)
        payment = payment_parts[0] if payment_parts else Spacer(1, 1)
        qr = self._qr_flowable(document, company, options, module_mm=_QR_MODULE_MM) or Spacer(1, 1)

        if not document.vat_liable:
            notice = Paragraph("<b>Podjetje ni zavezanec za DDV</b><br/>" + ARTICLE_94_NOTICE, look["art94"])
        else:
            notice = Paragraph("<b>DDV je obračunan skladno z veljavno stopnjo.</b>", look["art94"])

        cards = Table(
            [[payment, qr, notice]],
            colWidths=[86 * mm, 44 * mm, 60 * mm],
        )
        palette = resolve_palette(options)
        cards.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (0, 0), 0.55, palette["light_border"]),
            ("BOX", (1, 0), (1, 0), 0.55, palette["light_border"]),
            ("BOX", (2, 0), (2, 0), 0.55, palette["light_border"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        result = [Spacer(1, 2.0 * mm), stack, Spacer(1, 3.0 * mm), cards]
        if options.get("show_signature", True):
            # Thank-you copy lives in the footer left lockup only (no duplicate).
            sig = self._invoice_signature_block(company, options, 60)
            sig_row = Table(
                [[Spacer(1, 1), sig]],
                colWidths=[CONTENT_WIDTH_MM * mm - 60 * mm, 60 * mm],
            )
            sig_row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                *_NO_PADDING,
            ]))
            result += [Spacer(1, 2.0 * mm), sig_row]
        return result

    def _payment_block(self, document: PdfDocument, company: CompanyProfile, options: dict):
        """Payment details (+ UPN QR for invoices), sized for the closing left column."""
        if not self._has_payment(document):
            return []
        look = styles(options)
        palette = resolve_palette(options)
        method = document.payment_method or options.get("payment_method") or "Nakazilo"
        due_label = _due_label(document.doc_type)

        # QR is rendered by _closing_section below the payment details / Article 94 notice.
        # MASTER lower card width; keeps payment text inside the left card.
        pay_w = 82 * mm

        heading = Table(
            [
                [
                    bank_icon(palette, size=BANK_ICON_MM * mm),
                    Paragraph("Podatki za plačilo", look["section"]),
                ]
            ],
            colWidths=[(BANK_ICON_MM + 3) * mm, pay_w - (BANK_ICON_MM + 3) * mm],
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

        labelled: list[tuple[str, str]] = []
        if document.doc_type != "invoice":
            labelled.append(("Način plačila:", esc(method)))

        iban_text = format_iban(company.iban) or "—"
        bank = (getattr(company, "bank", "") or "").strip()
        if company.iban and bank:
            # Wrap only between the IBAN and the bank name, never inside either.
            iban_text = f"{iban_text} ({esc(bank).replace(' ', NBSP)})"
        labelled.append(("TRR:", iban_text))

        if document.doc_type != "invoice":
            labelled.append((f"{due_label}:", esc(format_date(document.due_date))))
        if document.doc_type == "invoice":
            sklic_raw = (document.reference or "").strip() or format_reference(document.number)
            labelled.append(("Sklic:", esc(format_reference_display(sklic_raw))))
            labelled.append(("Namen:", f"Plačilo računa št.{NBSP}{esc(document.number)}"))

        label_style = look["meta_label"]
        label_w = max(
            16 * mm,
            max(stringWidth(label, label_style.fontName, label_style.fontSize) for label, _ in labelled)
            + 2.5 * mm,
        )
        details = Table(
            [
                [Paragraph(label, label_style), Paragraph(value, look["body"])]
                for label, value in labelled
            ],
            colWidths=[label_w, pay_w - label_w],
        )
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

        pay_col = Table(
            [[heading], [Spacer(1, 3.0)], [details]],
            colWidths=[pay_w],
        )
        pay_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), *_NO_PADDING]))
        return [pay_col]

    def _invoice_signature_block(
        self,
        company: CompanyProfile,
        options: dict,
        width_mm: float,
    ):
        """Approved invoice sign-off: signer name, signature/rule, then role."""
        look = styles(options)
        palette = resolve_palette(options)
        signature_path = existing_path(options.get("signature_path", ""))
        signer = resolve_signer_name(company.name, options.get("signer_name", ""))

        name = Paragraph(f"<b>{esc(signer)}</b>", look["caption"]) if signer else Spacer(1, 1)
        role = Paragraph("Direktor", look["caption"])
        if signature_path:
            signature = image_or_space(
                signature_path,
                min(SIGNATURE_WIDTH_MM, max(width_mm - 8, 30)),
                SIGNATURE_HEIGHT_MM,
            )
        else:
            # Without a scanned signature reserve only a compact signing area;
            # the old 18 mm blank made the lower half look unfinished.
            signature = Spacer(1, 8.0 * mm)

        line_w = min(max(width_mm - 10, 34), 48)
        line = Table([[""]], colWidths=[line_w * mm], rowHeights=[2.5])
        line.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 0.8, palette["charcoal"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        rows = [[name], [signature], [line], [role]]
        block = Table(rows, colWidths=[width_mm * mm])
        block.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
                ]
            )
        )
        return block

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
        # Render the UPN QR as an embedded PNG. This is more reliable in Qt PDF
        # preview and Windows PDF viewers than thousands of tiny vector rectangles.
        side = 85 * float(module_mm) * mm
        png = BytesIO()
        code.save(png, kind="png", scale=6, border=4, dark="black", light="white")
        png.seek(0)
        drawing = Image(png, width=side, height=side)
        size = side
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

        Draws green line + signer name (when known) + role (Direktor).
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

        signer = resolve_signer_name(
            company.name if company is not None else "", options.get("signer_name", "")
        )
        name_para = (
            Paragraph(f"<b>{esc(signer)}</b>", look["sign_name"]) if signer else Spacer(1, 1)
        )
        role_para = Paragraph("Direktor", look["sign_role"])

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
