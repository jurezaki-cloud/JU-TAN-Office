# JU-TAN Office — Premium Document Redesign

**Date:** 2026-09-21  
**Scope:** Company branding + professional ERP PDF templates (invoices, offers, orders, delivery notes)

## Summary

Document branding (logo, signature, stamp, colors) is now stored in the SQLite `company` table. The shared ReportLab pipeline (`app/pdf/`) renders a modern branded layout for all commercial document types while keeping existing export APIs and settings toggles backward compatible.

## What changed

### 1. Database branding (migration)

New `company` columns (schema migration **v3** via `app/database/migrations.py` / `ensure_schema_version()`, with `CompanyRepository.ensure_schema()` safety net / fresh `CREATE TABLE`):

| Column | Purpose | Default |
|--------|---------|---------|
| `signature_path` | Director signature image | empty |
| `stamp_path` | Company stamp image | empty |
| `doc_primary_color` | Text / navy | `#0F172A` |
| `doc_accent_color` | Accent bars / rules | `#059669` |
| `doc_table_header_color` | Table / panel fill | `#F1F5F9` |

APIs:

- `company_repository.get_branding()`
- `company_repository.save_branding(...)`
- Legacy `settings.json` `pdf.signature_path` / `pdf.stamp_path` are copied into empty DB columns on schema ensure, and still used as runtime fallback.

### 2. Branding settings UI

`PdfCard` (Nastavitve → Dokumenti) now includes:

- Logo upload with preview (archived under `DATA_DIR/branding/`)
- Signature / stamp upload (archived to stable paths)
- Document color pickers (primary, accent, table header)
- Existing PDF toggles (logo/VAT/discounts/notes/signature/stamp DA-NE)

Saving settings calls `pdf_card.save_branding()` so branding persists in the database.

### 3. PDF template redesign

Shared engine improvements applied to **invoice / offer / order / delivery** (and travel orders header/footer):

| Area | Change |
|------|--------|
| Header | Accent bar + bordered company block with logo, contact, tax/registration, IBAN |
| Customer | Accent-edged information panel |
| Title meta | Compact boxed document meta |
| Items table | Brand table-header color + accent underline |
| Totals | Bordered panel, emphasized “Skupaj za plačilo” |
| Payment | Framed payment block; invoices place UPN QR beside payment details |
| Signature/stamp | Optional boxed slots; still **zero space** when both toggles are NE |
| Footer | Brand accent rule, thank-you message, clickable site, page number |

New helper: `app/pdf/pdf_branding.py` (palette resolution + asset archival).

### 4. Backward compatibility

- Export entry points unchanged: `pdf_export.export_invoice/offer/order/delivery`
- Settings toggles remain in `settings.json`
- Empty branding → previous default colors and line-based signature/stamp
- Settings JSON paths still accepted when DB paths are empty
- `_title_block` / `_customer_block` accept optional `options` for older call sites

## Verification

### Migration

```
db.initialize()
company_repository.ensure_schema()
→ get_branding() returns 6 fields; company row width = 28
```

### PDF export smoke test

Generated under `data/premium_pdf_test/`:

- `RAC-PREMIUM-1.pdf` (invoice)
- `PON-PREMIUM-1.pdf` (offer)
- `NAR-PREMIUM-1.pdf` (order)
- `DOB-PREMIUM-1.pdf` (delivery)

### Regression tests

```
pytest tests/test_production_stability.py tests/test_offers_module.py tests/test_vat_regime.py
→ 41 passed
```

## Key files

- `app/database/company_repository.py` — schema + branding CRUD
- `app/database/database.py` — fresh-install company DDL
- `app/pdf/pdf_branding.py` — colors + asset archive
- `app/pdf/pdf_company.py` — load company/options with DB branding
- `app/pdf/pdf_header.py` / `pdf_footer.py` / `pdf_tables.py` / `pdf_engine.py`
- `app/widgets/settings/pdf_card.py` — branding UI
- `app/modules/settings/settings_page.py` — persist branding on save

## How to use

1. Open **Nastavitve → Dokumenti**
2. Upload logo, signature, stamp; choose document colors
3. Click **Shrani**
4. Export any invoice / offer / order / delivery note — branding applies automatically
