"""PDF document header — large logo left, company info flush-right, accent separator."""

from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle

from app.pdf.pdf_branding import (
    CONTENT_WIDTH_MM,
    HEADER_TO_SEPARATOR_MM,
    LOGO_MAX_HEIGHT_MM,
    LOGO_MAX_WIDTH_MM,
    LOGO_MONOGRAM_FRAC,
    LOGO_TAGLINE_PULL_FRAC,
    SECTION_SPACING_MM,
    TAGLINE,
    TAGLINE_CHAR_SPACE,
    HeaderSeparator,
    SpacedTagline,
    contact_email_icon,
    contact_phone_icon,
    contact_web_icon,
    resolve_palette,
)
from app.pdf.pdf_images import pdf_image, resolve_pdf_logo_path
from app.pdf.pdf_styles import ensure_fonts, styles
from app.utils.flags import parse_bool


def _logo_brand_group(logo: Flowable, look: dict, palette: dict) -> Table:
    """Treat logo + tagline as one brand block; tagline under the wordmark only."""
    logo_w = float(getattr(logo, "drawWidth", LOGO_MAX_WIDTH_MM * mm) or LOGO_MAX_WIDTH_MM * mm)
    logo_h = float(getattr(logo, "drawHeight", LOGO_MAX_HEIGHT_MM * mm) or LOGO_MAX_HEIGHT_MM * mm)
    indent = logo_w * LOGO_MONOGRAM_FRAC
    word_w = max(logo_w - indent, 28 * mm)
    regular, _bold = ensure_fonts()
    tag = SpacedTagline(
        TAGLINE,
        word_w,
        font_name=regular,
        font_size=8.4,
        color=palette["muted"],
        char_space=TAGLINE_CHAR_SPACE,
        align="center",
    )
    tag_row = Table([[Spacer(indent, 1), tag]], colWidths=[indent, word_w])
    tag_row.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ]
        )
    )
    # Official logo PNGs include large bottom padding; pull tagline into that void
    # so it visually belongs to the JU-TAN wordmark (MASTER spacing).
    pull = -max(logo_h * LOGO_TAGLINE_PULL_FRAC, 18)
    group = Table(
        [[logo], [Spacer(1, pull)], [tag_row]],
        colWidths=[logo_w],
    )
    group.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 2), (0, 2), -10.0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    return group


def _contact_row(icon: Flowable, text: Paragraph, text_w: float) -> Table:
    row = Table([[icon, text]], colWidths=[13.5, text_w])
    row.hAlign = "RIGHT"
    row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 3.2),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0.45),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.45),
            ]
        )
    )
    return row


def build_header(company, options: dict):
    """Premium ERP header: large logo + flush-right company block + separator."""
    look = styles(options)
    palette = resolve_palette(options)
    content_w = CONTENT_WIDTH_MM * mm
    regular, _bold = ensure_fonts()

    logo_block: Flowable | Spacer
    if parse_bool(options.get("show_logo"), default=True):
        resolved = resolve_pdf_logo_path(getattr(company, "logo", "") or "")
        logo = None
        if resolved is not None:
            logo = pdf_image(str(resolved), LOGO_MAX_WIDTH_MM, LOGO_MAX_HEIGHT_MM)
        if logo is not None:
            logo_block = _logo_brand_group(logo, look, palette)
        else:
            logo_block = Spacer(LOGO_MAX_WIDTH_MM * mm, 12)
    else:
        logo_block = Spacer(LOGO_MAX_WIDTH_MM * mm, 10)

    city_line = " ".join(
        part for part in (company.postal_code, company.city) if part
    ).strip()
    if company.country:
        city_line = f"{city_line}, {company.country}".strip(", ")

    # Build a single right-aligned company column so every line shares one right edge.
    info_lines: list = [Paragraph(company.name or "JU-TAN Office", look["company"])]
    if company.address:
        info_lines.append(Paragraph(company.address, look["meta"]))
    if city_line:
        info_lines.append(Paragraph(city_line, look["meta"]))

    contact_entries = []
    phone = (company.phone or company.mobile or "").strip()
    if phone:
        contact_entries.append(
            (contact_phone_icon(palette, size=12.0), phone, Paragraph(phone, look["meta_contact"]))
        )
    if company.email:
        contact_entries.append(
            (
                contact_email_icon(palette, size=12.0),
                company.email,
                Paragraph(company.email, look["meta_contact"]),
            )
        )
    website = (getattr(company, "website", "") or "").strip()
    if website:
        display = website.replace("https://", "").replace("http://", "")
        contact_entries.append(
            (
                contact_web_icon(palette, size=12.0),
                display,
                Paragraph(display, look["meta_contact"]),
            )
        )

    tax = (company.tax_number or "").strip()
    reg = (getattr(company, "registration_number", "") or "").strip()

    # Width must fit the longest identity/TRR line so the right edge stays flush.
    _, bold = ensure_fonts()
    name_w = stringWidth(company.name or "JU-TAN Office", bold, 12.6)
    trr_w = 0.0
    iban_line = ""
    if company.iban:
        bank = (getattr(company, "bank", "") or "").strip()
        iban_line = f"TRR: {company.iban}"
        if bank:
            iban_line = f"{iban_line} ({bank})"
        trr_w = stringWidth(iban_line, regular, 10.0)
    info_width = max(name_w, trr_w, 76 * mm) + 4

    # Right-pack each contact independently so every value shares the same
    # right edge while its icon remains directly beside the text.
    if contact_entries:
        for icon, text, para in contact_entries:
            text_w = stringWidth(text, regular, 10.0) + 2
            inner_w = 13.5 + text_w
            spacer_w = max(info_width - inner_w, 1)
            row = _contact_row(icon, para, text_w)
            wrap = Table([[Spacer(spacer_w, 1), row]], colWidths=[spacer_w, inner_w])
            wrap.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0.25),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.25),
                    ]
                )
            )
            info_lines.append(wrap)

    if tax:
        info_lines.append(Paragraph(f"Davčna št.: {tax}", look["meta"]))
    if reg:
        info_lines.append(Paragraph(f"Matična št.: {reg}", look["meta"]))
    if iban_line:
        info_lines.append(Paragraph(iban_line, look["meta"]))

    info_block = Table([[line] for line in info_lines], colWidths=[info_width])
    info_block.hAlign = "RIGHT"
    info_block.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.7),
            ]
        )
    )

    logo_width = content_w - info_width
    body = Table(
        [[logo_block, info_block]],
        colWidths=[logo_width, info_width],
    )
    body.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    separator = HeaderSeparator(CONTENT_WIDTH_MM, palette, accent_mm=34)
    separator.hAlign = "LEFT"
    # MASTER separator ≈ 0.202 — keep logo/company block fixed; only air below body.
    return [
        body,
        Spacer(1, HEADER_TO_SEPARATOR_MM * mm),
        separator,
        Spacer(1, SECTION_SPACING_MM),
    ]
