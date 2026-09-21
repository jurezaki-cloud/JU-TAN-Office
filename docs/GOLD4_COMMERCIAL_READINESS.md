# GOLD-4 Commercial Readiness — License, Updates, Signing, Installer

**Date:** 2026-09-21  
**Product:** JU-TAN Office Enterprise 1.0.0 GOLD  
**Constraint:** No accounting / document-logic changes.

This document is the audit record for GOLD-4 commercial gates:
license activation security, device binding, online validation, update-channel readiness,
Authenticode preparation, and final installer production checks.

---

## 1. Current state (pre-patch baseline)

| Area | State before GOLD-4 hardening |
| --- | --- |
| Online licensing | Present: `licensing_service.py` → `https://ju-tan.com/api/v1/licenses`, DPAPI token, activate/validate/deactivate |
| Startup gate | `license_gate.ensure_licensed()` on app start; grace period if server unreachable |
| Device fingerprint | SHA-256(`MachineGuid\|hostname\|arch\|MAC`) sent on activate/validate |
| Device bind enforcement | **Missing locally** — stored `device_id` was not compared to current machine before grace |
| TLS | urllib default; **no explicit HTTPS gate** / SSL context |
| Offline HMAC license | `app.core.license` with embedded pepper — UI metadata only; **not** the startup gate |
| Updates | Local `updates/latest.json` only; empty `url`; **no** HTTPS feed, hash, or signature checks |
| Authenticode | Ready: `AuthenticodeSigning.ps1`, `build_release.ps1 -RequireSigned`, `docs/SIGNING.md` |
| Installer | Strong: AppMutex, CloseApplications, WAL pre-upgrade, docs, packs `latest.json` |

---

## 2. Missing parts addressed in GOLD-4

1. Local device-binding check + wipe on mismatch (no grace for stolen seats).
2. Reject plaintext activation tokens on Windows (DPAPI required).
3. HTTPS-only license API (localhost HTTP only with `JU_TAN_LICENSE_INSECURE=1`).
4. Explicit TLS default context + versioned User-Agent on license calls.
5. License key length/control-char validation.
6. Sync `APP_VERSION` from `app.core.constants` (removed hardcoded `"1.0.0"`).
7. Update manifest schema: `sha256`, `channel`, `signature`; HTTPS URL + hash required when downloading.
8. Optional remote feed `JU_TAN_UPDATE_URL` with local fallback.
9. HMAC manifest signing (`sign_update_manifest.ps1` + production verify key).
10. Installer production gate script `check_installer_production.ps1`.

---

## 3. Exact patches (files)

| File | Change |
| --- | --- |
| `app/services/licensing_service.py` | HTTPS gate, SSL context, device bind helpers, DPAPI-only tokens on Windows, key normalize, constants version |
| `app/services/license_gate.py` | Refuse / clear state when device not bound; re-activate prompt |
| `app/core/update.py` | Manifest validation, remote HTTPS feed, HMAC signature verify |
| `app/widgets/settings/update_card.py` | Surface `UpdateError` clearly |
| `updates/latest.json` | Extended schema (`sha256`, `channel`, `signature`) |
| `resources/update_keys/production/*` | HMAC verify key + README |
| `scripts/sign_update_manifest.ps1` | Sign `latest.json` |
| `scripts/check_installer_production.ps1` | Final production checks |
| `tests/test_commercial_readiness_gold4.py` | Contract + crypto unit tests |
| `docs/SECURITY.md` | Clarify online vs legacy offline license |
| `docs/GOLD4_COMMERCIAL_READINESS.md` | This audit |

---

## 4. Security risks (residual)

| Risk | Severity | Notes / mitigation |
| --- | --- | --- |
| Client HMAC update key extractable from binary | Medium | Expected for symmetric channel auth; **Authenticode on Setup.exe is primary trust** |
| Offline `app.core.license` pepper is forgeable | Medium | Not used by startup gate; do not treat as commercial entitlement |
| Device ID uses hostname + MAC (can change) | Low–Med | User may need re-activation after major hardware/network changes; MachineGuid is primary on Windows |
| Grace period allows offline use after last good validate | Low | By design; server must revoke seats / shorten grace for stricter policy |
| No cert pinning on license API | Low | Uses OS trust store via `ssl.create_default_context()` |
| Auto-download / apply of updates not implemented | Info | Channel readiness only; install still via signed Setup |
| PFX not in CI until secrets configured | Info | `-RequireSigned` hard-fails without `JU_TAN_PFX` |

---

## 5. Release checklist (GOLD-4)

### License / device

- [ ] Confirm production license API is HTTPS and reachable
- [ ] Smoke: activate → restart → validate OK
- [ ] Smoke: copy `license.json` to another machine → refused / re-activation
- [ ] Smoke: offline with valid `grace_until` still opens app
- [ ] Smoke: deactivate frees seat

### Update channel

- [ ] Keep `url` empty for 1.0.0 unless CDN is live
- [ ] When publishing a newer build: set `version`, HTTPS `url`, `sha256`, run `sign_update_manifest.ps1`
- [ ] Optional QA: `JU_TAN_UPDATE_REQUIRE_SIGNATURE=1`

### Authenticode

- [ ] Set `JU_TAN_PFX` (+ password) on release machine
- [ ] `.\scripts\build_release.ps1 -RequireSigned`
- [ ] `.\scripts\verify_release_signatures.ps1 -RequireSigned`
- [ ] Confirm publisher CN matches legal entity

### Installer / packaging

- [ ] `.\scripts\check_installer_production.ps1`
- [ ] After build: `.\scripts\check_installer_production.ps1 -RequireSignedArtifacts`
- [ ] Verify `dist/SHA256SUMS.txt` generated **after** signing
- [ ] Manual install upgrade: AppMutex closes app; WAL pre-upgrade backup present

### Regression (non-accounting)

- [ ] `pytest tests/test_commercial_readiness_gold4.py tests/test_release_readiness_p0.py -q`
- [ ] Existing gold/deployment suite as needed

---

## 6. Commands

```powershell
# Static production contract
.\scripts\check_installer_production.ps1

# Sign update manifest (when url/sha256 set)
.\scripts\sign_update_manifest.ps1 -Path updates\latest.json

# Production signed release
$env:JU_TAN_PFX = "C:\certs\ju-tan.pfx"
.\scripts\build_release.ps1 -RequireSigned
.\scripts\verify_release_signatures.ps1 -RequireSigned
.\scripts\check_installer_production.ps1 -RequireSignedArtifacts
```
