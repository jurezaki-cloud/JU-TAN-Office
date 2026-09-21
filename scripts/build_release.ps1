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
    5. Sign JU-TAN-Office-Setup.exe
    6. Generate dist/SHA256SUMS.txt (after all signing)
    7. Optionally verify Authenticode (release mode only)

  Certificate is NOT required for development/RC. Set JU_TAN_PFX for signed builds.
  Use -RequireSigned or JU_TAN_REQUIRE_SIGNED=1 for production release gates.

.PARAMETER RequireSigned
  Fail if Authenticode signing/verification cannot complete for required targets.
#>
[CmdletBinding()]
param(
    [switch]$RequireSigned
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

. "$PSScriptRoot\AuthenticodeSigning.ps1"

$require = Test-JuTanRequireSigned -RequiredSwitch:$RequireSigned
if ($require) {
    $ready = Test-JuTanSigningReady
    if (-not $ready.Ready) {
        throw "Release signed mode enabled, but signing is not ready: $($ready.Reason)"
    }
    Write-Host "Release signed mode: ON (Authenticode required)"
} else {
    Write-Host "Release signed mode: OFF (unsigned OK — development/RC)"
}

# Keep Version.txt / file_version_info / version.iss aligned with app.core.constants
python scripts/sync_release_metadata.py

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean packaging/ju-tan-office.spec

# --- 1) Sign application EXE before portable copy and before Inno packs it ---
$appExe = "dist/JU-TAN-Office/JU-TAN-Office.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller output missing: $appExe"
}
Invoke-AuthenticodeSign -Path $appExe -Required:$require

# --- 2) Portable tree from (possibly) signed app build ---
$portable = "dist/JU-TAN-Office-Portable"
if (Test-Path $portable) { Remove-Item $portable -Recurse -Force }
Copy-Item "dist/JU-TAN-Office" $portable -Recurse
New-Item -ItemType Directory -Force -Path "$portable/data","$portable/exports","$portable/logs","$portable/Backup","$portable/Temp","$portable/Reports","$portable/docs" | Out-Null
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

# Portable EXE is a copy of the signed app EXE — re-sign only if copy somehow lost signature
# (must complete before ZIP so the archive contains the signed binary).
$portableExe = "$portable/JU-TAN-Office.exe"
if (Test-Path -LiteralPath $portableExe) {
    $portSig = Get-AuthenticodeSignature -FilePath $portableExe
    if ($portSig.Status -ne "Valid") {
        $ready = Test-JuTanSigningReady
        if ($ready.Ready -or $require) {
            Invoke-AuthenticodeSign -Path $portableExe -Required:$require
        }
    } else {
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

function Write-Checksums {
    $sum = "dist/SHA256SUMS.txt"
    $lines = @()
    Get-ChildItem dist -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        $lines += "$hash  $($_.Name)"
    }
    $lines -join "`n" | Set-Content -Path $sum -Encoding ascii
    Write-Host "Checksums: $sum"
}

$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

# --- 3) Installer (packs signed app EXE) then sign Setup.exe ---
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "packaging/installer.iss"
    $setup = "dist/JU-TAN-Office-Setup.exe"
    if (-not (Test-Path -LiteralPath $setup)) {
        throw "Inno Setup finished but installer missing: $setup"
    }
    Copy-Item "packaging/Version.txt" "dist/Version.txt" -Force
    Copy-Item "docs/RELEASE_NOTES.md" "dist/RELEASE_NOTES.md" -Force -ErrorAction SilentlyContinue
    Invoke-AuthenticodeSign -Path $setup -Required:$require
    Write-Host "Installer: $setup"
} else {
    $msg = "Inno Setup ni nameščen — preskočen installer. Portable mapa je v dist/JU-TAN-Office-Portable"
    if ($require) {
        throw "Release signed mode requires Inno Setup 6 (ISCC.exe) to produce and sign JU-TAN-Office-Setup.exe. $msg"
    }
    Write-Host $msg
}

# --- 4) Checksums AFTER all signing ---
Write-Checksums

# --- 5) Release-mode signature gate ---
$verifyArgs = @()
if ($require) { $verifyArgs += "-RequireSigned" }
& "$PSScriptRoot\verify_release_signatures.ps1" @verifyArgs
if ($LASTEXITCODE -ne 0) {
    throw "Release signature verification failed (exit $LASTEXITCODE)."
}

Write-Host "Release build complete."
