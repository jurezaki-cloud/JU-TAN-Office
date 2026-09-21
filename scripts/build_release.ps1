#Requires -Version 5.1
<#
.SYNOPSIS
  Build JU-TAN Office release artifacts (PyInstaller + portable + Inno Setup).

.DESCRIPTION
  Build order (signing-ready):
    1. Sync metadata + build application (PyInstaller)
    2. Sign JU-TAN-Office.exe (optional unless -RequireSigned)
    3. Assemble portable tree + ZIP from the signed app tree
    4. Build installer (Inno packs already-signed EXE)
    5. Sign JU-TAN-Office-Setup.exe (Cert:\CurrentUser\My CN=JU-TAN Studio, or PFX fallback)
    6. Verify installer with signtool verify /pa /v
    7. Generate dist/SHA256SUMS.txt (after all signing)
    8. Optionally verify Authenticode suite (release mode only)

  Certificate is NOT required for development/RC. Production gate: -RequireSigned
  or JU_TAN_REQUIRE_SIGNED=1. Auto-discovers store cert and newest signtool.exe.

.PARAMETER RequireSigned
  Fail if Authenticode signing/verification cannot complete for required targets.
#>
[CmdletBinding()]
param(
    [switch]$RequireSigned
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptRoot
Set-Location -LiteralPath $RepoRoot

. (Join-Path $ScriptRoot "AuthenticodeSigning.ps1")

# ---------------------------------------------------------------------------
# Pipeline functions (release surface)
# Find-SignTool / Find-CodeSigningCertificate / Verify-Signature come from
# AuthenticodeSigning.ps1; Sign-Installer and Create-Checksum are defined here.
# ---------------------------------------------------------------------------

function Sign-Installer {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$Required
    )
    return Invoke-AuthenticodeSign -Path $Path -Required:$Required
}

function Create-Checksum {
    param(
        [string]$DistDir = "dist"
    )
    if (-not (Test-Path -LiteralPath $DistDir)) {
        throw "Cannot create checksums — dist folder missing: $DistDir"
    }
    $sum = "dist/SHA256SUMS.txt"
    $lines = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $DistDir -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()
        [void]$lines.Add("$hash  $($_.Name)")
    }
    ($lines -join "`n") + "`n" | Set-Content -Path $sum -Encoding ascii
    Write-Host "Checksums: $sum"
    return $sum
}

function Write-Stage {
    param([string]$Name, [string]$Status = "OK")
    Write-Host ("{0}:`n{1}`n" -f $Name, $Status)
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "================================"
Write-Host " JU-TAN OFFICE RELEASE PIPELINE"
Write-Host "================================"
Write-Host ""

$require = Test-JuTanRequireSigned -RequiredSwitch:$RequireSigned
if ($require) {
    $tool = Find-SignTool
    if (-not $tool) {
        throw "signtool.exe not found under 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe'. Install Windows SDK Signing Tools or set JU_TAN_SIGNTOOL. See docs/SIGNING.md."
    }
    $storeCert = Find-CodeSigningCertificate
    $ready = Test-JuTanSigningReady
    if (-not $ready.Ready) {
        throw "Release signed mode enabled, but signing is not ready: $($ready.Reason)"
    }
    Write-Host "Release signed mode: ON (Authenticode required)"
    Write-Host "  signtool: $tool"
    if ($storeCert) {
        Write-Host "  Certificate store: $($storeCert.Subject)"
        Write-Host "  Thumbprint: $($storeCert.Thumbprint)"
    }
    elseif ($ready.Mode -eq "Pfx") {
        Write-Host "  Certificate: PFX $($ready.PfxPath)"
    }
}
else {
    Write-Host "Release signed mode: OFF (unsigned OK — development/RC)"
}
Write-Host ""

# --- Building ---
python scripts/sync_release_metadata.py
if ($LASTEXITCODE -ne 0) { throw "sync_release_metadata.py failed (exit $LASTEXITCODE)." }

python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed (exit $LASTEXITCODE)." }

python -m PyInstaller --noconfirm --clean packaging/ju-tan-office.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)." }

$appExe = "dist/JU-TAN-Office/JU-TAN-Office.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller output missing: $appExe"
}
Write-Stage -Name "Building" -Status "OK"

# --- Documentation (pack into portable / dist) ---
$docSources = @(
    "docs/PRIVACY.md",
    "docs/INSTALL.md",
    "docs/USER_GUIDE.md",
    "docs/ADMIN_GUIDE.md",
    "docs/RELEASE_NOTES.md",
    "docs/SECURITY.md"
)
foreach ($rel in $docSources) {
    if (-not (Test-Path -LiteralPath $rel)) {
        throw "Required documentation missing: $rel"
    }
}
Write-Stage -Name "Documentation" -Status "OK"

# --- Sign application EXE before portable copy and before Inno packs it ---
Invoke-AuthenticodeSign -Path $appExe -Required:$require

# --- Portable tree from (possibly) signed app build ---
$portable = "dist/JU-TAN-Office-Portable"
if (Test-Path -LiteralPath $portable) { Remove-Item -LiteralPath $portable -Recurse -Force }
Copy-Item "dist/JU-TAN-Office" $portable -Recurse
New-Item -ItemType Directory -Force -Path @(
    "$portable/data", "$portable/exports", "$portable/logs",
    "$portable/Backup", "$portable/Temp", "$portable/Reports", "$portable/docs"
) | Out-Null
Copy-Item "packaging/Version.txt" "$portable/Version.txt" -Force
Copy-Item "packaging/LICENSE.txt" "$portable/LICENSE.txt" -Force
Copy-Item "docs/PRIVACY.md" "$portable/docs/PRIVACY.md" -Force
Copy-Item "docs/INSTALL.md" "$portable/docs/INSTALL.md" -Force
Copy-Item "docs/USER_GUIDE.md" "$portable/docs/USER_GUIDE.md" -Force
Copy-Item "docs/ADMIN_GUIDE.md" "$portable/docs/ADMIN_GUIDE.md" -Force
Copy-Item "docs/RELEASE_NOTES.md" "$portable/docs/RELEASE_NOTES.md" -Force
Copy-Item "docs/SECURITY.md" "$portable/docs/SECURITY.md" -Force
Copy-Item "docs/SIGNING.md" "$portable/docs/SIGNING.md" -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$portable/config" | Out-Null
Copy-Item "config/app.example.json" "$portable/config/app.example.json" -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path "dist" | Out-Null

$portableExe = "$portable/JU-TAN-Office.exe"
if (Test-Path -LiteralPath $portableExe) {
    $portSig = Get-AuthenticodeSignature -FilePath $portableExe
    if ($portSig.Status -ne "Valid") {
        $readyPort = Test-JuTanSigningReady
        # Self-signed store certs report UnknownError/NotTrusted — still treat as signed if thumbprint matches.
        $alreadySigned = $false
        if ($portSig.SignerCertificate -and $readyPort.Thumbprint) {
            $alreadySigned = ($portSig.SignerCertificate.Thumbprint -eq $readyPort.Thumbprint)
        }
        if (-not $alreadySigned -and ($readyPort.Ready -or $require)) {
            Invoke-AuthenticodeSign -Path $portableExe -Required:$require
        }
        elseif ($alreadySigned) {
            Write-Host "Portable EXE already signed: $portableExe"
        }
    }
    else {
        Write-Host "Portable EXE already signed: $portableExe"
    }
}

if (Test-Path "dist/JU-TAN-Office-Portable.zip") { Remove-Item "dist/JU-TAN-Office-Portable.zip" -Force }
Compress-Archive -Path $portable -DestinationPath "dist/JU-TAN-Office-Portable.zip"
Write-Host "Portable ZIP: dist/JU-TAN-Office-Portable.zip"

Copy-Item "packaging/Version.txt" "dist/Version.txt" -Force
Copy-Item "LICENSE.txt" "dist/LICENSE.txt" -Force
Copy-Item "docs/PRIVACY.md" "dist/PRIVACY.md" -Force
Copy-Item "docs/RELEASE_NOTES.md" "dist/RELEASE_NOTES.md" -Force -ErrorAction SilentlyContinue
Copy-Item "docs/USER_GUIDE.pdf" "dist/USER_GUIDE.pdf" -Force -ErrorAction SilentlyContinue
Copy-Item "docs/ADMIN_GUIDE.pdf" "dist/ADMIN_GUIDE.pdf" -Force -ErrorAction SilentlyContinue

# --- Installer ---
$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$setup = "dist/JU-TAN-Office-Setup.exe"

if ($iscc) {
    & $iscc "packaging/installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed (exit $LASTEXITCODE)." }
    if (-not (Test-Path -LiteralPath $setup)) {
        throw "Inno Setup finished but installer missing: $setup"
    }
    Copy-Item "packaging/Version.txt" "dist/Version.txt" -Force
    Copy-Item "docs/RELEASE_NOTES.md" "dist/RELEASE_NOTES.md" -Force -ErrorAction SilentlyContinue
    Write-Stage -Name "Installer" -Status "OK"
}
else {
    $msg = "Inno Setup ni nameščen — preskočen installer. Portable mapa je v dist/JU-TAN-Office-Portable"
    if ($require) {
        throw "Release signed mode requires Inno Setup 6 (ISCC.exe) to produce and sign JU-TAN-Office-Setup.exe. $msg"
    }
    Write-Host $msg
    Write-Stage -Name "Installer" -Status "SKIPPED (ISCC not found)"
}

# --- Certificate readiness (report stage) ---
$certReady = Test-JuTanSigningReady
$null = Find-SignTool
$null = Find-CodeSigningCertificate
if ($certReady.Ready) {
    Write-Stage -Name "Certificate" -Status "OK"
}
elseif ($require) {
    throw "Certificate: FAIL — $($certReady.Reason)"
}
else {
    Write-Stage -Name "Certificate" -Status "SKIPPED (dev/RC unsigned OK)"
}

# --- Sign + verify installer ---
if (Test-Path -LiteralPath $setup) {
    Sign-Installer -Path $setup -Required:$require
    if ($certReady.Ready -or $require) {
        Write-Stage -Name "Signing" -Status "OK"
        Verify-Signature -Path $setup -Required:($require -or $certReady.Ready)
        Write-Stage -Name "Verification" -Status "OK"
    }
    else {
        Write-Stage -Name "Signing" -Status "SKIPPED (dev/RC unsigned OK)"
        Write-Stage -Name "Verification" -Status "SKIPPED (dev/RC unsigned OK)"
    }
}
elseif ($require) {
    throw "Installer missing for signing: $setup"
}
else {
    Write-Stage -Name "Signing" -Status "SKIPPED (no installer)"
    Write-Stage -Name "Verification" -Status "SKIPPED (no installer)"
}

# --- Checksums AFTER all signing ---
Create-Checksum -DistDir "dist" | Out-Null
Write-Stage -Name "Checksum" -Status "OK"

# --- Release-mode signature gate (suite) ---
$verifyArgs = @()
if ($require) { $verifyArgs += "-RequireSigned" }
& (Join-Path $ScriptRoot "verify_release_signatures.ps1") @verifyArgs
if ($LASTEXITCODE -ne 0) {
    throw "Release signature verification failed (exit $LASTEXITCODE)."
}

Write-Host "================================"
Write-Host " RELEASE READY"
Write-Host "================================"
Write-Host ""
Write-Host "Release build complete."
