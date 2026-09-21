# Code signing — JU-TAN Office (Authenticode)

This document describes **release signing** for Windows binaries. It does **not** change application logic, database, licensing, authentication, or document workflows.

**Development builds never require a certificate.** Running `python app.py` or an unsigned `build_release.ps1` is supported.

## Signing targets

| Artifact | Path | When signed |
| --- | --- | --- |
| Application EXE | `dist/JU-TAN-Office/JU-TAN-Office.exe` | After PyInstaller, **before** portable copy and Inno Setup |
| Installer | `dist/JU-TAN-Office-Setup.exe` | After Inno Setup |
| Portable EXE | `dist/JU-TAN-Office-Portable/JU-TAN-Office.exe` | Copied from the signed app EXE (re-signed only if status ≠ Valid) |

The portable ZIP (`dist/JU-TAN-Office-Portable.zip`) is not Authenticode-signed (ZIP is not a PE image). The EXE inside the ZIP is signed.

SHA-256 checksums (`dist/SHA256SUMS.txt`) are generated **after** all signing so hashes match shipped files.

## Build order (required)

```
1. Build application          (PyInstaller)
2. Sign JU-TAN-Office.exe
3. Assemble portable + ZIP    (from signed tree)
4. Build installer            (Inno packs signed EXE)
5. Sign JU-TAN-Office-Setup.exe
6. Generate SHA256SUMS.txt
7. Verify signatures          (hard-fail only in release mode)
```

Implemented by `scripts/build_release.ps1`.

## Environment variables

| Variable | Required? | Purpose |
| --- | --- | --- |
| `JU_TAN_PFX` | Only for signed builds | Path to code-signing PFX |
| `JU_TAN_PFX_PASSWORD` | If PFX is password-protected | PFX password |
| `JU_TAN_TIMESTAMP_URL` | Optional | RFC 3161 timestamp URL (default `http://timestamp.digicert.com`) |
| `JU_TAN_SIGNTOOL` | Optional | Full path to `signtool.exe` if SDK discovery fails |
| `JU_TAN_REQUIRE_SIGNED` | Optional | `1` / `true` / `yes` → fail when signing/verification cannot complete |

## Scripts

| Script | Role |
| --- | --- |
| `scripts/AuthenticodeSigning.ps1` | Shared helpers: PFX checks, timestamp URL, signtool discovery, `Invoke-AuthenticodeSign` |
| `scripts/sign_authenticode.ps1` | CLI wrapper to sign one or more files |
| `scripts/verify_release_signatures.ps1` | Report status + publisher; `-RequireSigned` fails release if signatures missing/invalid |
| `scripts/build_release.ps1` | Full release pipeline (optional or required signing) |
| `scripts/build_portable.ps1` | Portable-only build with optional EXE signing |

### signtool discovery

`Find-SignTool` searches, in order:

1. `JU_TAN_SIGNTOOL` if set and present
2. Windows Kits 10/11 `bin\<version>\(x64|arm64|x86)\signtool.exe` (newest version first)
3. Legacy `bin\x64\signtool.exe` layouts
4. `signtool.exe` on `PATH`

Clear errors are raised when release mode is on but PFX is missing, the PFX path is invalid, signtool is missing, or `signtool sign` returns non-zero.

## Development / RC (unsigned OK)

```powershell
# No certificate — build succeeds unsigned
.\scripts\build_release.ps1

# Advisory verification (does not fail on unsigned)
.\scripts\verify_release_signatures.ps1
```

## Production signed release

```powershell
$env:JU_TAN_PFX = "C:\certs\ju-tan.pfx"
$env:JU_TAN_PFX_PASSWORD = "***"
# optional:
# $env:JU_TAN_TIMESTAMP_URL = "http://timestamp.digicert.com"
# $env:JU_TAN_SIGNTOOL = "C:\Path\To\signtool.exe"

# Either switch:
.\scripts\build_release.ps1 -RequireSigned

# Or environment gate:
$env:JU_TAN_REQUIRE_SIGNED = "1"
.\scripts\build_release.ps1
```

Manual sign (same order as the build script):

```powershell
.\scripts\sign_authenticode.ps1 -Path dist\JU-TAN-Office\JU-TAN-Office.exe -Required
# … ISCC packaging/installer.iss …
.\scripts\sign_authenticode.ps1 -Path dist\JU-TAN-Office-Setup.exe -Required
.\scripts\verify_release_signatures.ps1 -RequireSigned
```

## Verification steps

1. After a signed release build:

```powershell
.\scripts\verify_release_signatures.ps1 -RequireSigned
```

2. Or with Windows tools:

```powershell
signtool verify /pa dist\JU-TAN-Office\JU-TAN-Office.exe
signtool verify /pa dist\JU-TAN-Office-Setup.exe
Get-AuthenticodeSignature dist\JU-TAN-Office-Setup.exe |
  Select-Object Status, StatusMessage, @{n='Publisher';e={$_.SignerCertificate.Subject}}
```

3. Expected: `Status = Valid`, publisher CN matching the legal name on the certificate (typically **JU-TAN Studio** or the OV/EV organization on the cert).

4. Confirm checksums were regenerated after signing:

```powershell
Get-Content dist\SHA256SUMS.txt
Get-FileHash dist\JU-TAN-Office-Setup.exe -Algorithm SHA256
```

### Release mode failure conditions

With `-RequireSigned` / `JU_TAN_REQUIRE_SIGNED=1`, verification **fails** if:

- `dist/JU-TAN-Office/JU-TAN-Office.exe` is missing or not `Valid`
- `dist/JU-TAN-Office-Setup.exe` exists but is not `Valid`
- `dist/JU-TAN-Office-Portable/JU-TAN-Office.exe` exists but is not `Valid`
- Signing prerequisites (PFX / signtool) are not ready during `build_release.ps1 -RequireSigned`

Without release mode, the same checks are **advisory** only (exit 0) so development stays unblocked.

## Publisher metadata

Installer and VersionInfo already carry `AppPublisher`, support/web URLs, and copyright. The Authenticode subject should match the legal name on the code-signing certificate.

## Security notes

- Never commit PFX files or passwords to the repository.
- Prefer CI secret stores / hardware tokens for production keys.
- Timestamping keeps signatures verifiable after the cert expires.
