# Release freeze preparation — JU-TAN Office 1.0.0 GOLD

**Date:** 2026-09-21  
**Branch:** `main` @ `0b0160c` (tracking `origin/main`)  
**Version:** `APP_VERSION=1.0.0` / `APP_CHANNEL=GOLD` / `SCHEMA_VERSION=3`  
**Scope of this step:** classify working tree for freeze — **no build, no tag, no functional code changes**.

---

## 1. Git status summary

| Category | Count (approx.) | Notes |
| --- | --- | --- |
| Modified tracked files | ~65 | App UI, settings, packaging, docs, build scripts, tests |
| Deleted tracked | 1 | `packaging/SHA256SUMS.txt` (intentional — checksums live under `dist/` only) |
| Untracked (release-intended) | ~25+ | Core release helpers, signing scripts, privacy/signing docs, widgets, release tests |
| Untracked / ignored (QA temp) | local only | `.rc-qa-tmp/`, `.audit-tmp/`, `tmp_ui2.xml`, probe scripts |

Working tree is **not frozen in git yet** (nothing staged/committed by this prep). Freeze commit remains a follow-up after review.

---

## 2. Separation: intended release vs temporary

### Included for release (must ship / must be committed)

#### Release-critical (verified present)

| Area | Path | Git state |
| --- | --- | --- |
| Release metadata | `app/core/release_meta.py` | **untracked — include** |
| Installer mutex | `app/core/app_mutex.py` | **untracked — include** |
| Docs path helper | `app/core/docs_paths.py` | **untracked — include** |
| Splash branding | `app/core/ui/splash_branding.py` | **untracked — include** |
| Signing library | `scripts/AuthenticodeSigning.ps1` | **untracked — include** |
| Sign entry | `scripts/sign_authenticode.ps1` | **untracked — include** |
| Verify signatures | `scripts/verify_release_signatures.ps1` | **untracked — include** |
| Metadata sync | `scripts/sync_release_metadata.py` | **untracked — include** |
| Release build | `scripts/build_release.ps1` | modified — include |
| Portable build | `scripts/build_portable.ps1` | modified — include |
| Privacy doc | `docs/PRIVACY.md` | **untracked — include** |
| Signing doc | `docs/SIGNING.md` | **untracked — include** |
| Security doc | `docs/SECURITY.md` | modified — include |
| Installer | `packaging/installer.iss` | modified — include |
| Inno version defs | `packaging/version.iss` | **untracked — include** |
| PyInstaller spec | `packaging/ju-tan-office.spec` | modified — include |
| Version info | `packaging/file_version_info.txt` | modified — include |
| Version banners | `Version.txt`, `packaging/Version.txt` | modified — include |
| Release readiness tests | `tests/test_release_readiness_p0.py` | **untracked — include** |
| Deployment / gold tests | `tests/test_deployment.py`, `tests/test_qa_gold.py` | modified — include |

Packaging references confirmed:

- `packaging/installer.iss` → `AppMutex`, PRIVACY / SECURITY / SIGNING docs
- `packaging/ju-tan-office.spec` → PRIVACY, SECURITY, SIGNING (+ other release docs)

#### Broader intended product surface (also part of this freeze set)

- Settings / licensing UI: `settings_page.py`, `settings_controller.py`, license/privacy/update/health cards, `licensing_service.py`, `license_gate.py`
- First-run / main / dashboard: `first_run_wizard.py`, `main_window.py`, `dashboard.py`, `app/widgets/dashboard/*`
- Document editor widgets: `app/widgets/document_editor/*`
- List chrome / search / theme: enterprise search, list status bar, theme.qss/theme.py, page chrome
- CRM list polish (invoices / offers / orders pages & widgets)
- Docs: `CHANGELOG`, `RELEASE_NOTES`, `RELEASE_REPORT`, `GOLD_CERT`, INSTALL/USER/ADMIN guides, README, root `INSTALL.md`
- UI tests: `test_first_run_wizard_ui.py`, `test_settings_*`, `test_ui_render_perf.py`
- Ignore hygiene: `.gitignore` (audit/QA excludes)

### Excluded from release (temporary / local QA)

| Path | Action taken |
| --- | --- |
| `tmp_ui2.xml` | **Removed** from tree + added to `.gitignore` |
| `.rc-qa-tmp/` | Left on disk (local ProgramData probes/backups) + added to `.gitignore` |
| `.audit-tmp/` | Already ignored (unchanged) |
| `scripts/_perf_startup_probe.py` | Local probe — covered by new `scripts/_perf_*.py` ignore |
| `__pycache__/`, `.pytest_cache/` | Already ignored |
| `dist/`, `build/`, `logs/`, `*.log`, `data/*` runtime | Already ignored |
| `packaging/SHA256SUMS.txt` | Intentionally deleted; regenerated as `dist/SHA256SUMS.txt` by build |

---

## 3. Freeze hygiene actions completed

1. Reviewed `git status` on `main`.
2. Separated release-intended paths from QA/temp artifacts (above).
3. Ignored / removed temp QA:
   - `tmp_ui2.xml` — deleted + ignored
   - `.rc-qa-tmp/` — ignored (not deleted; contains local install/upgrade probe artifacts)
4. Verified release-critical files exist on disk and are referenced by packaging/tests.
5. This report written; **build not run; tag not created**.

---

## 4. Remaining risks (pre-build / pre-tag)

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Large uncommitted freeze set not yet reviewed line-by-line | High | Diff review + commit freeze before build |
| Authenticode unsigned without `JU_TAN_PFX` / `-RequireSigned` | Medium | Expected for RC; production gate via `docs/SIGNING.md` |
| `.rc-qa-tmp` still on disk | Low | Ignored; delete locally when probes no longer needed |
| UI / settings / document-editor changes are large surface | Medium | Run `tests/test_release_readiness_p0.py`, `test_qa_gold.py`, settings/first-run UI tests before build |
| Release date in metadata still `2026-09-12` | Low | Confirm intentional before tag; sync via `scripts/sync_release_metadata.py` if changed |
| No freeze commit / tag yet | Info | By design for this prep step |

---

## 5. Recommended next steps (not done here)

1. Stage **only** intended paths (exclude anything still temp).
2. Commit freeze on `main` (or release branch) when approved.
3. Run release test suite (at least P0 + gold/deployment).
4. Then `scripts/build_release.ps1` (optionally `-RequireSigned`).
5. Tag only after artifacts + checksums verified.

---

## 6. Checklist — release-critical inclusion

- [x] `app/core/release_meta.py`
- [x] `app/core/app_mutex.py`
- [x] Signing scripts (`AuthenticodeSigning.ps1`, `sign_authenticode.ps1`, `verify_release_signatures.ps1`)
- [x] Privacy / security docs (`docs/PRIVACY.md`, `docs/SECURITY.md`, `docs/SIGNING.md`)
- [x] Installer changes (`packaging/installer.iss`, `packaging/version.iss`, spec, build scripts)
- [x] Release tests (`tests/test_release_readiness_p0.py` + deployment/gold updates)
- [x] Temp QA excluded (`tmp_ui2.xml`, `.rc-qa-tmp`)
- [ ] Freeze commit
- [ ] Release build
- [ ] Tag
