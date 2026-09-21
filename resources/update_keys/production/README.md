# Production update-channel verification key (HMAC-SHA256)

This directory holds the **client-side verification material** for `updates/latest.json`
(and remote feeds pointed to by `JU_TAN_UPDATE_URL`).

## Trust model (GOLD-4 readiness)

1. **Primary trust:** Authenticode on `JU-TAN-Office-Setup.exe` / app EXE (`docs/SIGNING.md`).
2. **Channel integrity:** HMAC-SHA256 over the canonical JSON manifest (field `signature`).
3. **Payload integrity:** `sha256` of the downloadable installer when `url` is set (HTTPS only).

HMAC verification keys shipped with the client can be extracted from the binary.
They stop casual CDN/path tampering of `latest.json`; they are **not** a substitute for
Authenticode on the installer.

## Files

| File | Purpose |
| --- | --- |
| `manifest_hmac.hex` | 32-byte key as hex — used by `app.core.update` to verify `signature` |
| `README.md` | This document |

## Release signing

```powershell
$env:JU_TAN_UPDATE_HMAC_KEY = (Get-Content resources\update_keys\production\manifest_hmac.hex -Raw).Trim()
.\scripts\sign_update_manifest.ps1 -Path updates\latest.json
```

For production rotation, generate a new key, update `manifest_hmac.hex`, re-sign the
manifest, and ship both in the next signed release.

## Strict mode

Set `JU_TAN_UPDATE_REQUIRE_SIGNATURE=1` to refuse downloadable manifests without a valid
`signature` (used in production gate scripts / QA).
