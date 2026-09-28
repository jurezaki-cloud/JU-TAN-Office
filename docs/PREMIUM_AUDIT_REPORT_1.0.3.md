# JU-TAN Office Enterprise — Premium Product Audit Report

**Branch:** `audit/premium-redesign-1.0.3`  
**Rollback:** `backup/pre-premium-audit-20260928`  
**Date:** 2026-09-28  
**Version baseline:** 1.0.2 GOLD

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

### Legend

- **DONE** — implemented and verified  
- **IMPROVED** — better, not exhaustive  
- **NOT CHANGED** — intentionally preserved  
- **RECOMMENDED FOR LATER** — out of safe scope or needs interactive hardware/signing  
