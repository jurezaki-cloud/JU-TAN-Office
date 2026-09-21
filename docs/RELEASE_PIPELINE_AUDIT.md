# Phase 1 — Release Pipeline Audit

**Date:** 2026-09-21  
**Repo:** JU-TAN Office (`main`)  
**Auditor:** Release engineering pass (pre-implementation)

---

## Release steps (current)

| Step | Mechanism | Status |
| --- | --- | --- |
| 1. Metadata sync | `scripts/sync_release_metadata.py` → Version.txt, version.iss, file_version_info | OK |
| 2. Dependencies | `pip install -r requirements.txt` | OK |
| 3. App build | PyInstaller `packaging/ju-tan-office.spec` | OK |
| 4. Sign app EXE | `Invoke-AuthenticodeSign` via PFX (`JU_TAN_PFX`) | Partial — PFX only, not Cert:\ store |
| 5. Portable tree + ZIP | Copy signed tree, docs, Version.txt | OK |
| 6. Installer | Inno Setup 6 `ISCC.exe` → `dist/JU-TAN-Office-Setup.exe` | OK (if ISCC present) |
| 7. Sign installer | Same PFX path | Partial — same gap |
| 8. SHA256 | `Write-Checksums` → `dist/SHA256SUMS.txt` | OK |
| 9. Verify | `verify_release_signatures.ps1` (hard-fail only with `-RequireSigned`) | OK |
| 10. Docs PDF | `scripts/write_gold_guides.py` (manual / separate) | Separate from build script |
| 11. Cleanup | Removes prior portable dir / ZIP before recreate | OK |
| 12. Production gate | `scripts/check_installer_production.ps1` | OK (static) |

## Findings before changes

1. **Signing source:** Pipeline depends on `JU_TAN_PFX` file env vars. Certificate `CN=JU-TAN Studio` already exists in `Cert:\CurrentUser\My`, but build does not auto-discover it.
2. **Script root:** `build_release.ps1` uses `$PSScriptRoot` (good) but sets location relative to parent; Phase 3 asks for explicit `$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path` and `Set-StrictMode`.
3. **Banner / stage output:** No structured RELEASE PIPELINE status banner.
4. **signtool path:** Discovery exists in `AuthenticodeSigning.ps1`; Phase 2 requires explicit Windows Kits `\*\x64\signtool.exe` newest + hard fail when missing in release mode.
5. **Verification:** PowerShell `Get-AuthenticodeSignature` is used; Phase 2 also requires `signtool verify /pa /v` after installer sign.
6. **Tests:** `tests/test_release_readiness_p0.py` covers signing docs; no dedicated `tests/test_release_pipeline.py` for function presence / version consistency.
7. **Tag `v1.0.0`:** Points to `9d6928a` (GOLD final production hardening). HEAD is `aa15a4a` (PDF regen for schema v3) — **1 commit ahead**. Do not delete tag; re-tag or move only after explicit release decision.
8. **Docs drift:** `docs/RELEASE_FREEZE_PREP.md` still lists `SCHEMA_VERSION=2` while app uses `SCHEMA_VERSION = 3`. ADMIN/USER guides already say schema 3; PDFs were regenerated on HEAD.
9. **No `SCHEMA_VERSION = 1` leftovers** in docs (asserted by existing tests).

## Planned Phase 2–5 work

- Prefer automatic signing from `Cert:\CurrentUser\My` (`CN=JU-TAN Studio` / thumbprint).
- Keep PFX env vars as production-migration / CI fallback (backward compatible).
- Refactor `build_release.ps1` with StrictMode, named functions, stage banner.
- Update `docs/SIGNING.md` and add `tests/test_release_pipeline.py`.
- Fix freeze-prep schema note; regenerate guide PDFs if needed.

---

*This audit file is the Phase 1 report. Implementation follows in subsequent phases.*
