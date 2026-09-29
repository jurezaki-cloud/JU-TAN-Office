# JU-TAN Office Enterprise — Premium Product Audit Report

**Branch:** `audit/premium-redesign-1.0.3`  
**Rollback:** `backup/pre-premium-audit-20260928`  
**Date:** 2026-09-28  
**Version baseline:** 1.0.2 GOLD

> **Status 2026-09-29:** §1–§17 describe the first premium pass. The final release-gate
> verification in **§19** supersedes their test, build and installer results.

---

## 1. EXECUTIVE SUMMARY

Root-cause fix and premium polish pass on JU-TAN Office (PySide6 + SQLite).

The critical Offer/Invoice editor defect — **“+ Dodaj postavko” looking disabled while enabled** — was a stylesheet collision: `#DocumentEditorSplitter QWidget { background: transparent }` overrode `PrimaryButton` fills, leaving white text on a transparent surface.

Document editor, button hierarchy, customer card, items empty state, table formatting, and invoice/offer PDF polish were improved without changing accounting rules or database schema.

**Tests:** **394 passed / 0 failed / 0 skipped**  
**compileall:** OK  
**Visual QA:** Document editor screenshots + invoice/offer/multipage PDF renders inspected  
**Build:** Portable PyInstaller run attempted (see §15)

---

## 2. UI/UX CHANGES

| Area | Status | Notes |
| --- | --- | --- |
| Document editor cards | DONE | `DocumentItemsPanel` / `Customer` / `Totals` regain SURFACE chrome |
| Items empty state | DONE | Compact professional empty state + CTA |
| Add-item gating | DONE | Disabled with “Najprej izberite stranko.” when no customer |
| Customer card | IMPROVED | Address / contact hierarchy when available |
| Items table | IMPROVED | Numeric right-align, EUR/% formatting, column widths |
| Button hierarchy | IMPROVED | Primary / Secondary / Danger / Ghost states hardened |
| Sidebar | IMPROVED | Clearer keyboard focus on nav items |
| Global theming tokens | NOT CHANGED | Existing spacing/color tokens reused |
| Full module visual pass | IMPROVED | Highest-impact editor/PDF paths; remaining modules recommended later |

---

## 3. ICON SYSTEM CHANGES

| Change | Status |
| --- | --- |
| Keep existing brand stroke icons | NOT CHANGED (correct choice — no new dependency) |
| Primary CTA icons white on green | DONE |
| Danger outline icons use DANGER color (not white) | DONE |
| Add button text no longer duplicates “+” glyph | DONE |

---

## 4. DOCUMENT EDITOR CHANGES

- Restored card surfaces for items / customer / totals panels
- Compact empty state when 0 postavk
- Hint banner when add is blocked
- Table row height / hover / selection polish via QSS
- Invoice / offer / order dialogs share the same gating helper pattern

---

## 5. “+ DODAJ POSTAVKO” FIX

### Why it looked disabled

1. `theme.qss` rule `#DocumentEditorSplitter QWidget { background: transparent }` matched `QPushButton`
2. Specificity tied `QPushButton#PrimaryButton`; the splitter rule came **later**, so **transparent background won**
3. Primary text/icon stayed `ON_PRIMARY` (`#FFFFFF`) → white on page background ≈ invisible/ghosted
4. Amplifiers: overwriting `DocumentEditorCard` objectName removed card surface; header “Shrani” (outside splitter) looked correct, making the items CTA look uniquely broken

### How it was fixed

1. Removed broad transparent paint on all splitter descendants
2. Re-asserted PrimaryButton fills with explicit `#DocumentItemsPanel` / `#DocumentWorkspace` selectors + `background-color`
3. Restored card QSS for document panels
4. When disabled for missing customer, show explicit reason — never fake an enabled look

---

## 6. INVOICE PDF CHANGES

| Item | Status |
| --- | --- |
| Header contact icon alignment (shared baseline / packing) | DONE |
| Short green accent on main separator (`accent_mm=0`) | DONE |
| Remove horizontal green accent inside customer frame | DONE |
| Signer forced to **Tanja Hrup** (never “JU-TAN studio”) | DONE |
| Role label **Direktor** | DONE |
| Signature unit shifted toward totals / right | DONE |
| Payment block pulled closer (safe positive clearance; no overlap) | DONE |
| UPN QR semantics | NOT CHANGED |
| Footer / fold / Art. 94 | NOT CHANGED |

---

## 7. OFFER PDF CHANGES

Same signature / payment / header / customer-frame fixes as invoices. Offers continue without UPN QR.

---

## 8. PERFORMANCE OPTIMIZATIONS

| Item | Status |
| --- | --- |
| Avoided graphics drop-shadow reintroduction | NOT CHANGED (already correct) |
| No reckless query/schema changes | NOT CHANGED |
| Perceived speed via clearer empty/disabled states | IMPROVED |

Evidence-based only — no micro-optimization without measurement.

---

## 9. BUGS FOUND AND FIXED

1. Primary CTA washed out under document splitter QSS  
2. DangerButton icons rendered white on transparent outline buttons  
3. `extract_signer_name("JU-TAN studio")` could print studio as signer  
4. Negative payment spacer overlapped totals (“Direktor” into Za plačilo) on multipage last pages  
5. Version/docs drift (1.0.2 vs tests/docs asserting 1.0.1 / missing report mention)

---

## 10. DATABASE / ARCHITECTURE IMPROVEMENTS

**NOT CHANGED** — no schema migrations in this pass. Data integrity preserved.

---

## 11. ACCESSIBILITY IMPROVEMENTS

- Enabled vs disabled button contrast clarified  
- Disabled add action explains why  
- Sidebar nav focus style reinforced  
- Keyboard tooltips on add/remove  
- Tab order preserved via existing EnterpriseDialog patterns  

---

## 12. FILES CHANGED

- `app/theme/theme.qss`
- `app/core/ui/icons.py`
- `app/widgets/document_editor/items_panel.py`
- `app/widgets/document_editor/customer_panel.py`
- `app/widgets/invoices/invoice_table.py`
- `app/modules/invoices/models/invoice_items_model.py`
- `app/modules/invoices/invoice_dialog.py`
- `app/modules/offers/offer_dialog.py`
- `app/modules/orders/order_dialog.py`
- `app/pdf/pdf_branding.py`
- `app/pdf/pdf_engine.py`
- `app/pdf/pdf_header.py`
- `docs/CHANGELOG.md`
- `docs/RELEASE_REPORT.md`
- `tests/test_premium_document_editor.py` (new)
- `tests/test_deployment.py`
- `tests/test_pdf_invoice_redesign.py`
- `.gitignore`

---

## 13. TEST RESULTS

```
394 passed, 0 failed, 0 skipped
```

(`pytest -q`, `QT_QPA_PLATFORM=offscreen`, ~211s)

New regressions covered: QSS splitter safety, items empty/CTA gating, signer extraction, items model alignment.

---

## 14. VISUAL QA RESULTS

| Check | Result |
| --- | --- |
| Document workspace empty state | DONE — green primary CTAs visible |
| Invoice PDF 1-page | DONE — Direktor / Tanja Hrup / payment / totals |
| Offer PDF 1-page | DONE |
| Multipage invoice last page | DONE — no Direktor/totals overlap after spacer fix |
| Light theme editor | DONE (default) |
| Dark theme full app | RECOMMENDED FOR LATER (not fully launched interactively) |
| Live Windows GUI at 125%/150% DPI | RECOMMENDED FOR LATER |
| Login / license / backup interactive | RECOMMENDED FOR LATER |

Artifacts under `Temp/visual-qa/` (local only, gitignored).

---

## 15. BUILD RESULT

**DONE** — `scripts/build_portable.ps1` succeeded.

- Output: `dist/JU-TAN-Office/` and `dist/JU-TAN-Office-Portable/`
- EXE Authenticode signed (certificate store thumbprint present)
- Existing Desktop GOLD Setup.exe installers were **not** overwritten

---

## 16. INSTALLER RESULT

**NOT CHANGED** — Inno Setup installer (`build_release.ps1`) not rebuilt in this pass.  
Run signed release packaging when ready; do not replace last known-good Setup until smoke-tested.

---

## 17. REMAINING ISSUES

1. Dark-theme interactive sweep of every module  
2. High-DPI (125/150%) manual matrix  
3. Full payment-block vertical rhythm vs MASTER may still want a calibrated mm tweak per real company logo height  
4. Offer PDF TRR empty when company IBAN missing in runtime options (data, not layout)  
5. Installer rebuild + Authenticode  

---

## 18. RECOMMENDED FUTURE IMPROVEMENTS

1. Unified button factory helper for all module toolbars  
2. Shared document-editor empty-state component for purchase dialogs  
3. Automated screenshot CI for PrimaryButton under splitter  
4. MASTER mm harness asserting payment Y landmarks  
5. Complete icon audit on warehouse / CRM / automation modules  

---

## 19. FINAL RELEASE-GATE VERIFICATION (2026-09-29)

**Verified source:** `audit/premium-redesign-1.0.3` at `56897a1` plus the uncommitted working tree
(491 files, tree SHA-256 `f67022c1f32ec1cc1487141729fc20bafa434c7e593ef994ea15511a8d91baf2`).
Built from an isolated copy (`C:\Users\jurez\JU-TAN-Office-RC-build2`); the copy and the working tree
were hash-identical after the build.

**Verdict: RELEASE CANDIDATE.** Not GOLD: the 150 % DPI gate has one open defect, and the installer
and installed-app gates could not be executed on this machine.

### Gate matrix

| Gate | Result | Evidence | Blocking? |
| --- | --- | --- | --- |
| Automated tests | PASS | 467 passed, 0 failed, 0 skipped | No |
| compileall | PASS | exit 0 (`app`, `tests`, `scripts`, `app.py`) | No |
| Light-theme visual QA | PASS | Real Windows platform, 52 screens × 3 scales, 0 clipped / cut / overlapping / overflowing / surface patches | No |
| Dark-theme interactive QA | PASS | Same sweep in dark incl. dialogs, dropdown, message box, editor flow, theme switch and back; hover states by in-process tests | No |
| 100 % DPI | PASS | 0 findings; editor items table fits | No |
| 125 % DPI | PASS | 0 findings; editor items table fits (HEAD scrolled here) | No |
| 150 % DPI | FAIL | Editor items table scrolls horizontally by 318 px (open issue 1); travel orders 3 px squeeze (harmless) | Blocks GOLD, not RC |
| Invoice PDF | PASS | 11 invoice cases, 0 verifier failures, UPN decoded | No |
| Offer PDF | PASS | Signature / payment / header checks, no QR | No |
| Multipage PDF | PASS | 10 / 35 items, long names, mixed VAT: no missing or duplicated rows, no overlap, QR on last page only | No |
| Portable build | PASS | Built from verified copy; onedir exe = portable exe = exe in zip | No |
| Fresh Setup.exe build | PASS | Inno Setup 6.7.3, all 242 files from the verified copy; static installer checks passed | No |
| Installer test | NOT TESTED | No Windows Sandbox / Hyper-V; production 1.0.3 with the same AppId is installed here | Blocks GOLD |
| Installed-app smoke test | NOT TESTED | Same reason; activation needs the production license service | Blocks GOLD |
| Startup / log check | PASS | Frozen portable, 2 starts: Slovenian activation dialog after 0.5 s, clean logs, graceful exit 0, no writes outside the test root. Frozen DB init is behind activation: NOT TESTED | No |
| Artifact consistency | PASS | source → copy → build → portable → setup by hash; setup → installed NOT TESTED | No |

### Fixes in the release-gate phase (uncommitted)

- **Data safety:** one database shutdown path (`db_lifecycle.py`) before any file operation; fresh reset fails closed if files remain.
- **Installer:** pre-upgrade backup incl. WAL/SHM, app-close gate, backup-first wipe with verification (fail closed).
- **PDF:** user text escaped; UPN payload made ISO-8859-2 safe. HEAD crashed on typographic quotes in a payer name; the other 10 payloads are byte-identical to HEAD. Also:
  - header icons, separator and customer frame without green accents;
  - "Direktor" / "Tanja Hrup" centred under the totals;
  - payment block about 24 mm higher, with no overlap;
  - VAT breakdown per rate.
- **Theme:** themed check / radio / chevron SVGs, Danger hover tints with 4.5:1 labels, icon re-tint on theme switch, Slovenian Qt standard buttons.
- **Layout and DPI:**
  - Articles toolbar filter, wizard welcome and toolbar centring;
  - details panels scroll instead of squeezing;
  - payments table minimum height, 13-character VAT IDs;
  - stale grid height after re-layout;
  - five layout containers that painted the page background on cards.
- **Startup:** the app icon is set before the license gate, so the activation dialog no longer shows a generic icon.

### Release artifacts (not published; the known-good `dist/` build is untouched)

| File | Size (bytes) | SHA-256 |
| --- | --- | --- |
| `JU-TAN-Office-Setup.exe` | 44,262,048 | `2AFC9774DD4A0A1F1616427822B40B4BE1AF60D56A78939F9448A4EDCB17B17B` |
| `JU-TAN-Office-Portable.zip` | 61,120,070 | `55865A0F1398386745D0365A07F81EE6467D4441B1CF797771FC55E84F937D31` |
| `JU-TAN-Office.exe` (onedir = portable) | 8,446,480 | `CF8BD42BF243E66AAB30BF845E0AF160FFE029B9BA51033238B7F45A79AE8946` |

Location: `C:\Users\jurez\JU-TAN-Office-RC-build2\dist\`. FileVersion 1.0.3.0 / ProductVersion 1.0.3,
Authenticode self-signed `CN=JU-TAN Studio`, timestamped.

### Open issues

1. **150 % editor items table.** At 1280×680 logical the invoice / offer / order items table scrolls horizontally.
   - Cause: the customer panel's minimum width is 499 px, set by the side-by-side "Datum izdaje / Rok plačila" row. The splitter therefore cannot give the items pane its designed share.
   - This is pre-existing and needs a layout decision, for example stacking the fields and tuning the split.
2. **Installer changes are untested at runtime.** The new Setup.exe contains the installer data-safety changes above, which so far have only static checks. Test in a disposable VM or Windows Sandbox before distribution.
3. **Self-signed code signing.** Customers will see an untrusted publisher and SmartScreen warnings.
4. **Release label.** Release metadata labels this build "1.0.3 GOLD / GOLD RELEASE" (`APP_CHANNEL`, `Version.txt`).
5. **Minor findings:**
   - the UI shows "41.00 €" while PDFs show "41,00 €";
   - ISO dates in the payments and offers details;
   - elided payments columns at 150 %;
   - F4 does not open the calendar;
   - the PDF page number sits 3.6 mm from the bottom edge;
   - generic buttons are 48 px tall next to 33 px inputs;
   - travel orders are 3 px squeezed at 150 %.

---

### Legend

- **DONE** — implemented and verified  
- **IMPROVED** — better, not exhaustive  
- **NOT CHANGED** — intentionally preserved  
- **RECOMMENDED FOR LATER** — out of safe scope or needs interactive hardware/signing  
