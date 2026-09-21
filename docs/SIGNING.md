# Code signing — JU-TAN Office (Authenticode)

This document describes **release signing** for Windows binaries. It does **not** change application logic, database, licensing, authentication, or document workflows.

**Development builds never require a certificate.** Running `python app.py` or an unsigned `build_release.ps1` is supported. Production releases use `-RequireSigned`.

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
6. Verify installer           (signtool verify /pa /v)
7. Generate SHA256SUMS.txt
8. Verify signatures suite    (hard-fail only in release mode)
```

Implemented by `scripts/build_release.ps1`.

## How the certificate is created

### Development / internal (self-signed)

On the release machine (PowerShell as the signing user):

```powershell
$cert = New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject "CN=JU-TAN Studio" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeyExportPolicy Exportable `
  -KeySpec Signature `
  -NotAfter (Get-Date).AddYears(1)

$cert | Format-List Subject, Thumbprint, NotAfter
```

Notes:

- Subject **must** contain `CN=JU-TAN Studio` (exact substring used by `Find-CodeSigningCertificate`).
- Self-signed certs silence SmartScreen only for machines that trust the cert; end users may still see warnings until a public CA OV/EV cert is used.

### Production (public CA OV/EV)

1. Purchase an **Organization Validation (OV)** or **Extended Validation (EV)** code-signing certificate for the legal entity **JU-TAN Studio** (or matching registered name).
2. Complete CA identity verification.
3. Install the issued certificate into `Cert:\CurrentUser\My` (or the service account used by the release pipeline) **with the private key**.
4. Prefer hardware token / HSM for EV; exportable soft keys only when policy allows.

## How a developer installs the certificate

### Option A — Certificate store (preferred for local release)

1. Receive a `.pfx` (or install from token/smartcard software).
2. Double-click the PFX **or** run:

```powershell
$password = Read-Host -AsSecureString "PFX password"
Import-PfxCertificate `
  -FilePath "C:\certs\ju-tan-studio.pfx" `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -Password $password
```

3. Confirm:

```powershell
Get-ChildItem Cert:\CurrentUser\My |
  Where-Object { $_.Subject -like "*CN=JU-TAN Studio*" } |
  Format-List Subject, Thumbprint, HasPrivateKey, NotAfter
```

4. Ensure `HasPrivateKey = True` and `NotAfter` is in the future.

### Option B — PFX path (CI / migration fallback)

Keep the PFX file outside the repo and set:

```powershell
$env:JU_TAN_PFX = "C:\certs\ju-tan-studio.pfx"
$env:JU_TAN_PFX_PASSWORD = "***"   # if protected
```

Never commit PFX files or passwords.

## How release signing works

`scripts/build_release.ps1` + `scripts/AuthenticodeSigning.ps1`:

1. **`Find-SignTool`** — newest `signtool.exe` under  
   `C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe`  
   (override with `JU_TAN_SIGNTOOL`).
2. **`Find-CodeSigningCertificate`** — `Cert:\CurrentUser\My` where Subject contains `CN=JU-TAN Studio`; uses **Thumbprint**.
3. If no store cert: fall back to **`JU_TAN_PFX`** (backward compatible).
4. Sign with:

```text
signtool sign /fd SHA256 /td SHA256 /tr <timestamp> /sha1 <THUMBPRINT> <file.exe>
```

(or `/f` + optional `/p` for PFX mode). Default timestamp URL: `http://timestamp.digicert.com` (`JU_TAN_TIMESTAMP_URL` to override).

5. After `dist/JU-TAN-Office-Setup.exe` is created, **`Sign-Installer`** signs it and **`Verify-Signature`** runs `signtool verify /pa /v`.
6. **`Create-Checksum`** writes `dist/SHA256SUMS.txt`.

### Production signed release

```powershell
# Certificate already in Cert:\CurrentUser\My (CN=JU-TAN Studio)
.\scripts\build_release.ps1 -RequireSigned

# Or environment gate:
$env:JU_TAN_REQUIRE_SIGNED = "1"
.\scripts\build_release.ps1
```

Expected console stages:

```text
================================
 JU-TAN OFFICE RELEASE PIPELINE
================================

Building:
OK

Documentation:
OK

Installer:
OK

Certificate:
OK

Signing:
OK

Verification:
OK

Checksum:
OK

================================
 RELEASE READY
================================
```

If `signtool` or the certificate is missing in `-RequireSigned` mode, the build **stops** with a clear error (see messages referencing `docs/SIGNING.md`).

### Development / RC (unsigned OK)

```powershell
.\scripts\build_release.ps1
.\scripts\verify_release_signatures.ps1
```

## How verification works

1. **During release** (after installer sign):

```powershell
signtool verify /pa /v dist\JU-TAN-Office-Setup.exe
```

Failure fails the release when signing was required / certificate was used.

2. **Suite check**:

```powershell
.\scripts\verify_release_signatures.ps1 -RequireSigned
```

Reports Status + Publisher for app EXE, Setup, and portable EXE.

3. **Manual / PowerShell**:

```powershell
Get-AuthenticodeSignature dist\JU-TAN-Office-Setup.exe |
  Select-Object Status, StatusMessage, @{n='Publisher';e={$_.SignerCertificate.Subject}}
```

Expected: `Status = Valid`, publisher CN **JU-TAN Studio** (or the OV/EV organization on the production cert).

**Self-signed note:** `signtool verify /pa` reports *root not trusted* for self-signed `CN=JU-TAN Studio` certificates. The release pipeline still accepts the file when the signer thumbprint matches the store certificate (integrity OK) and prints a warning. Production OV/EV certificates must pass `/pa` without that fallback.

4. Confirm checksums after signing:

```powershell
Get-Content dist\SHA256SUMS.txt
Get-FileHash dist\JU-TAN-Office-Setup.exe -Algorithm SHA256
```

### Release mode failure conditions

With `-RequireSigned` / `JU_TAN_REQUIRE_SIGNED=1`, verification **fails** if:

- `signtool.exe` cannot be found
- No `CN=JU-TAN Studio` store cert **and** no valid `JU_TAN_PFX`
- `dist/JU-TAN-Office/JU-TAN-Office.exe` is missing or not `Valid`
- `dist/JU-TAN-Office-Setup.exe` exists but is not `Valid` / `signtool verify` fails
- `dist/JU-TAN-Office-Portable/JU-TAN-Office.exe` exists but is not `Valid`

Without release mode, checks are **advisory** so development stays unblocked.

## Environment variables

| Variable | Required? | Purpose |
| --- | --- | --- |
| *(store cert)* | Preferred for local release | `CN=JU-TAN Studio` in `Cert:\CurrentUser\My` |
| `JU_TAN_PFX` | Fallback / CI | Path to code-signing PFX |
| `JU_TAN_PFX_PASSWORD` | If PFX password-protected | PFX password |
| `JU_TAN_TIMESTAMP_URL` | Optional | RFC 3161 timestamp URL |
| `JU_TAN_SIGNTOOL` | Optional | Full path to `signtool.exe` |
| `JU_TAN_CERT_SUBJECT` | Optional | Subject needle (default `CN=JU-TAN Studio`) |
| `JU_TAN_REQUIRE_SIGNED` | Optional | `1` / `true` / `yes` → fail when signing/verification cannot complete |

## Scripts

| Script | Role |
| --- | --- |
| `scripts/AuthenticodeSigning.ps1` | `Find-SignTool`, `Find-CodeSigningCertificate`, `Invoke-AuthenticodeSign`, `Verify-Signature` |
| `scripts/sign_authenticode.ps1` | CLI wrapper to sign one or more files |
| `scripts/verify_release_signatures.ps1` | Report status + publisher; `-RequireSigned` fails release if signatures missing/invalid |
| `scripts/build_release.ps1` | Full pipeline: `Sign-Installer`, `Create-Checksum`, stage banner |
| `scripts/build_portable.ps1` | Portable-only build with optional EXE signing |

## Production certificate migration notes

| Stage | Action |
| --- | --- |
| Today (internal) | Self-signed or test cert `CN=JU-TAN Studio` in CurrentUser\My |
| Near production | Import CA-issued soft cert into the same store (same Subject/CN if possible) |
| Hardened production | Move private key to EV token/HSM; keep signing via store thumbprint (`/sha1`) |
| CI | Prefer non-interactive token + `JU_TAN_SIGNTOOL`, or PFX in a secret store via `JU_TAN_PFX` |
| Cutover | Rebuild + re-sign installer; regenerate `SHA256SUMS.txt`; re-run `verify_release_signatures.ps1 -RequireSigned` |
| Trust | Distribute root/intermediate only as required by enterprise policy — never ship private keys |

Timestamping keeps signatures verifiable after the signing certificate expires.

## Publisher metadata

Installer and VersionInfo already carry `AppPublisher`, support/web URLs, and copyright. The Authenticode subject should match the legal name on the code-signing certificate (**JU-TAN Studio**).

## Security notes

- Never commit PFX files or passwords to the repository.
- Prefer CI secret stores / hardware tokens for production keys.
- Timestamping keeps signatures verifiable after the cert expires.
- Limit who can export private keys from `Cert:\CurrentUser\My`.
