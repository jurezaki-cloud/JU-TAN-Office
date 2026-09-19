# JU-TAN OFFICE — FINAL ENGINEERING REPORT

## 1. EXECUTIVE SUMMARY

JU-TAN Office is a **PySide6 + SQLite** desktop business application (not a React/web stack). Baseline before this pass: **96 tests passed**, GOLD 1.0.0 packaging already present, but several production-facing gaps remained: mock analytics/dashboard charts, a dead **Offer → Invoice** button, settings errors masked as “coming soon”, float-only money math, no payment ledger / partial payments, and no real UPN QR on invoices.

This pass **implemented and verified** those gaps, unified EUR calculations, hardened RBAC/recovery paths already in progress, localized the shell to Slovenian, and re-verified automated tests plus a full **PyInstaller production build**.

**Final verified condition:** `105 passed` automated tests; `python -m compileall app` OK; PyInstaller COLLECT build **succeeded** (`dist/JU-TAN-Office/JU-TAN-Office.exe`).

Follow-up from [Audit critical production gaps](a86047a7-d581-4a35-bd8e-f2b514c81bd6) / [Audit UI/UX and design system](de2ac44e-c7b4-4031-b92a-defad29c4907): re-enabled unlock login (P0), stripped secrets from settings export, locked role escalation to `users`, restricted Read Only pages, Excel VAT reverse-split, invoice `Izdan` on save/PDF.

## 2. BEFORE VS AFTER

| Area | Before | After |
| --- | --- | --- |
| Tests | 96 passed | **103 passed** |
| Build | Existing GOLD dist | **PyInstaller rebuild OK** |
| Functionality | Offer→invoice placeholder; full-pay only | Conversion + partial/full payment ledger |
| Architecture | Scattered float totals | Central `app/utils/money.py` |
| UI/UX | Mixed EN/SL nav; mock charts | Slovenian shell; real-data charts/KPIs |
| Documents | PDF without payment QR | UPN QR when IBAN+amount present |
| Data integrity | No payments table | Safe `CREATE TABLE IF NOT EXISTS payments` |
| Security | Partial WIP RBAC | Role page gating + crash DB recovery retained/extended |
| Performance | No new N+1 introduced for money | Dashboard unpaid loop is O(n) over invoices (acceptable for desktop) |

## 3. CRITICAL ISSUES FOUND

1. **Dead Offer → Invoice action** — `offer_page.convert_invoice` showed “bo dodana kmalu”  
   - Impact: flagship workflow incomplete  
   - Root cause: unfinished feature  
   - Solution: full conversion copying items, numbering, status `Sprejeta` / invoice `Izdan`

2. **Mock revenue / analytics samples** — dashboard + analytics fell back to fake series  
   - Impact: prototype signal; false business picture  
   - Root cause: empty-data placeholders treated as product data  
   - Solution: empty charts/lists; real KPIs only

3. **Inconsistent money math** — float × VAT duplicated in dialogs/SQL  
   - Impact: rounding drift risk across editor/DB/PDF  
   - Root cause: no shared money module  
   - Solution: Decimal half-up helpers + `document_totals` / `recalculate_totals`

4. **Payments were status notes only** — `mark_paid` + note line; no ledger  
   - Impact: no partial payment / remaining balance  
   - Root cause: index on missing table; no repository  
   - Solution: `payments` table + `PaymentRepository` + dialog amount entry

5. **Settings failures showed PLACEHOLDER** — restore/import/export  
   - Impact: silent/misleading errors  
   - Solution: `handle_error` with real exception context

6. **No payment QR** — invoices lacked machine-readable payment data  
   - Solution: ZBS-style UPN QR payload (length checksum), rendered only with valid IBAN+amount

## 4. BUGS FIXED

### FRONTEND
- Silent save when no customer/items → toast validation (invoice/offer/order)
- Sidebar/toolbar English leftovers → Slovenian labels
- Dashboard KPI set replaced with unpaid/overdue (real)

### BACKEND/API
- N/A HTTP API (desktop); service/repository RBAC gates retained/extended

### DATABASE
- Added `payments` table + index on initialize
- Invoice recalculation via Python money totals (not fragile SQL float expression)

### BUSINESS LOGIC
- Offer → invoice conversion
- Partial / full payment status sync (`Delno plačan` / `Plačan`)

### FINANCIAL CALCULATIONS
- Shared Decimal EUR helpers; editors + item dialog + recalculate wired

### DOCUMENTS
- Invoice PDF UPN QR; SI00 reference normalization

### UI/UX
- `#TotalValue` emphasis; empty chart message; analytics “Ni podatkov” captions

### SECURITY
- Role-based page visibility; export/print require; path `ensure_inside` for PDF; crash recovery rollback

### PERFORMANCE
- No major regression; analytics N+1 item scan for top articles unchanged (pre-existing)

## 5. MISSING FUNCTIONALITY IMPLEMENTED

- Offer → Invoice conversion
- Partial payments with remaining balance
- Status **Delno plačano** in badges/filters
- UPN QR on invoice PDF
- Central money utility + tests
- Dashboard unpaid/overdue KPIs from live invoices
- Design system doc (`docs/DESIGN_SYSTEM.md`)

## 6. MODULES REBUILT

- **Payment dialog** — amount entry + ledger (justified: prior UX could only “mark paid”)
- **Analytics empty-data path** — remove mocks (justified: prototype signal)
- **Dashboard KPI strip** — business-useful unpaid/overdue (justified: fake-feeling customer/article counts as primary KPIs)

No wholesale rewrite of stable repositories/UI frameworks.

## 7. DATABASE CHANGES

- **Migration style:** `CREATE TABLE IF NOT EXISTS payments (...)` inside `Database.initialize` (non-destructive)
- Columns: `invoice_id`, `paid_date`, `amount`, `method`, `notes`, timestamps
- Index: `idx_payments_invoice`
- **Data safety:** existing DBs gain table on next start; no DROP/reset; no data deletion

## 8. BUSINESS LOGIC VERIFICATION

| Area | Result |
| --- | --- |
| Customers | Existing CRUD preserved; RBAC write gates |
| Products/articles | Preserved |
| Offers | Money totals + conversion verified by tests |
| Invoices | Money totals + PDF smoke export |
| VAT/discounts | Discount supported in money helper/DB; **line discount UI still mostly 0%** (editor does not expose discount spin yet) |
| Totals | Shared `document_totals` |
| Payments | Partial/full ledger tests pass |
| Statuses | Badge + Delno plačano |
| Numbering | Default prefix INV→**RAC** aligned with company schema |

## 9. UI/UX REBUILD

- Design tokens documented; TotalValue strengthened
- Shell nav/toolbar Slovenian
- Dashboard real KPIs + empty chart state
- Tables/status badges extended for partial pay
- Responsive tests still green (`test_responsive_ui`)
- Accessibility: existing dialogs/labels retained; no WCAG certification claimed

## 10. OFFER / INVOICE EDITOR

- Totals via money module
- Validation toasts for missing customer/items
- Item dialog uses `line_gross`
- Conversion from offer list action implemented

## 11. DOCUMENT / PDF / PRINT SYSTEM

- Invoice PDF export smoke: file written successfully
- UPN QR rendered when IBAN present; omitted otherwise (no fake QR)
- Logo/signature/stamp paths remain settings-driven (unchanged)
- Long multi-page stress: **not exhaustively GUI-tested** in this environment
- Bank-app scan of QR: **manual verification required**

## 12. SECURITY AUDIT

**Found/fixed (this branch):** placeholder errors hiding failures; PDF path escape; export/print permission; role page gating; post-crash integrity/rollback.

**Remaining risks:** local single-user model; installer Authenticode unsigned (pre-existing); automation email/python hooks still log placeholders; no formal pen-test.

## 13. PERFORMANCE

- Removed mock-data generation paths
- Dashboard refresh computes unpaid/overdue with per-invoice `get_by_id` (fine for typical SME volumes; optimize later if needed)

## 14. TEST RESULTS

COMMAND: `$env:QT_QPA_PLATFORM="offscreen"; pytest -q`  
RESULT: `103 passed in ~2.9s`  
PASS/FAIL: **PASS**  
NOTES: Baseline was 96; added money + finance workflow tests

COMMAND: `python -m compileall -q app`  
RESULT: OK  
PASS/FAIL: **PASS**

COMMAND: PDF export smoke script  
RESULT: PDF written (~700KB with QR)  
PASS/FAIL: **PASS**

## 15. BUILD RESULTS

TYPECHECK: N/A (Python project; no mypy gate in repo)  
LINT: No project-wide ruff/flake8 script; compileall used as syntax gate  
TEST: **103 passed**  
PRODUCTION BUILD: `python -m PyInstaller --noconfirm packaging/ju-tan-office.spec` → **Build complete** (`dist/JU-TAN-Office`)

## 16. WORKFLOWS VERIFIED

| Flow | Status | Notes |
| --- | --- | --- |
| A Customer→Offer→PDF→Invoice→Payment→Dashboard | **PARTIALLY VERIFIED** | Automated pieces + conversion/payment/money tests; full GUI click-path not driven |
| B Invoice + VAT + partial/full pay | **VERIFIED** (automated) | `test_finance_workflows` |
| C Search/filter | **PARTIALLY VERIFIED** | Existing module tests; no new breakage |
| D Validation errors | **PARTIALLY VERIFIED** | Toast paths added; UI not screenshot-tested |

## 17. RESPONSIVE QA

- Automated `tests/test_responsive_ui.py` **passed**
- Manual viewport sweep (1920/1440/1366/tablet/mobile) **NOT VERIFIED** in this headless session

## 18. FILES CHANGED

Important new/updated modules:

- `app/utils/money.py` — EUR Decimal math
- `app/database/payment_repository.py` — payment ledger
- `app/pdf/upn_qr.py` — UPN QR payload
- `app/modules/offers/offer_page.py` — conversion
- `app/modules/payments/payment_dialog.py` — partial pay UI
- `app/windows/dashboard.py` — real unpaid/overdue KPIs
- `app/modules/analytics/*` — mock removal
- `app/pdf/pdf_engine.py` / `pdf_export.py` — QR + reference
- Security/RBAC: `permissions.py`, `main_window.py`, `db_guard.py`, settings pages
- Tests: `tests/test_money.py`, `tests/test_finance_workflows.py`

## 19. DEPENDENCIES

- **Added:** none required for money/QR (stdlib Decimal + reportlab QR already available)
- **Prior WIP:** `argon2-cffi` already in `requirements.txt` from security workstream
- **Removed:** none
- **Upgraded:** none in this pass

## 20. REMAINING RISKS

- UPN QR bank-app acceptance needs human scan test (ECI/ISO-8859-2 nuances)
- Line-item **discount UI** still defaults to 0% (backend supports discount)
- Automation email/python hooks remain placeholders by design
- Legal/accounting compliance (e-račun, FURS, etc.) **not claimed**
- Multi-user concurrency beyond SQLite WAL assumptions
- Headless session could not fully visually QA every page

## 21. MANUAL VERIFICATION REQUIRED

1. Launch GUI: create offer → convert → open invoice → PDF → scan UPN QR in banking app  
2. Record partial then full payment; confirm list badges + dashboard unpaid  
3. Settings restore with a bad file — confirm real error text  
4. Role = Sales/Warehouse — confirm hidden modules  
5. Visual pass at 1366×768 and 1920×1080  
6. Accountant review of VAT/totals wording on printed invoices  

## 22. RECOMMENDED NEXT STEPS

### CRITICAL
- Manual UPN QR scan validation with real IBAN

### IMPORTANT
- Expose line discount % in item dialog (wired to money helper)
- Optimize dashboard unpaid calculation (join instead of N gets)
- Optional: wire settings numbering yearly_reset into `get_next_number`

### OPTIONAL
- Authenticode signing of Setup.exe  
- Deeper multi-page PDF stress fixtures  
- Replace remaining automation placeholders when integrations exist  

## 23. FINAL STATUS

**IMPLEMENTATION SUBSTANTIALLY COMPLETE — REMAINING ITEMS LISTED ABOVE**

Evidence supports: tests green, production PyInstaller build green, core financial/payment/conversion/PDF gaps closed. Full interactive GUI and legal/QR bank acceptance remain human-gated.
