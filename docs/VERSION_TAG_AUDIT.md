# Phase 6 — Version and tag audit

**Date:** 2026-09-21  
**Repository:** JU-TAN-Office  
**Branch:** `main`

---

## Current tag

| Field | Value |
| --- | --- |
| Tag | `v1.0.0` |
| Commit | `9d6928a8445be16d233e03d97d06f1d2b95bf639` |
| Subject | GOLD final production hardening |

## Current HEAD

| Field | Value |
| --- | --- |
| HEAD | `aa15a4aad9e3e678ec1b4c3e55b997371ebe106e` |
| Subject | docs: regenerate GOLD PDFs for schema v3 |
| Commits ahead of `v1.0.0` | **1** (+ any uncommitted release-pipeline work after this audit) |

## Comparison

`v1.0.0` does **not** point at HEAD. The tagged commit is one documentation-only commit behind `main` (PDF regeneration for schema v3), plus subsequent release-pipeline hardening on the working tree after this report was drafted.

**Tag was NOT deleted** (per release policy).

## Recommended action

1. Finish and commit the release-pipeline signing/docs/test updates on `main`.
2. Run a full signed build: `.\scripts\build_release.ps1 -RequireSigned`.
3. Choose one:
   - **Preferred for a clean 1.0.0 line:** move the annotated tag after release artifacts are verified:

```powershell
git tag -a v1.0.0 HEAD -m "JU-TAN Office 1.0.0 GOLD production release" -f
git push origin v1.0.0 --force
```

   Only force-update the remote tag with explicit maintainer approval.
   - **Safer alternative:** leave `v1.0.0` on `9d6928a` and publish the next ship as `v1.0.1` (or `v1.0.0-gold2`) from HEAD after the signed build.

4. Do **not** delete `v1.0.0` automatically.

## App version constants (HEAD)

| Constant | Value |
| --- | --- |
| `APP_VERSION` | `1.0.0` |
| `APP_CHANNEL` | `GOLD` |
| `SCHEMA_VERSION` | `3` |
