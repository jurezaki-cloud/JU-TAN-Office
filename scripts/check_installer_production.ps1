#Requires -Version 5.1
<#
.SYNOPSIS
  Final installer / commercial production readiness checks (GOLD-4).

.DESCRIPTION
  Static contract checks for packaging, signing scripts, update channel,
  and license-related release docs. Does not build or change accounting logic.

.PARAMETER RequireSignedArtifacts
  Also require dist/ Authenticode Valid signatures (post-build gate).

.PARAMETER RequireUpdateSignature
  Fail if updates/latest.json has a non-empty url without a valid signature.
#>
[CmdletBinding()]
param(
    [switch]$RequireSignedArtifacts,
    [switch]$RequireUpdateSignature
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$failures = New-Object System.Collections.Generic.List[string]

function Assert-True([bool]$Cond, [string]$Msg) {
    if (-not $Cond) { [void]$failures.Add($Msg) }
}

Write-Host "=== JU-TAN Office GOLD-4 installer production checks ==="

# --- Core packaging
Assert-True (Test-Path "packaging/installer.iss") "Missing packaging/installer.iss"
Assert-True (Test-Path "packaging/version.iss") "Missing packaging/version.iss"
Assert-True (Test-Path "packaging/ju-tan-office.spec") "Missing packaging/ju-tan-office.spec"
Assert-True (Test-Path "packaging/LICENSE.txt") "Missing packaging/LICENSE.txt"
Assert-True (Test-Path "packaging/Version.txt") "Missing packaging/Version.txt"
Assert-True (-not (Test-Path "packaging/SHA256SUMS.txt")) "Stale packaging/SHA256SUMS.txt must not ship (checksums live under dist/)"

$iss = Get-Content "packaging/installer.iss" -Raw
Assert-True ($iss -match 'AppMutex=JU-TANOfficeMutex') "installer.iss missing AppMutex=JU-TANOfficeMutex"
Assert-True ($iss -match 'CloseApplications=yes') "installer.iss missing CloseApplications=yes"
Assert-True ($iss -match 'pre-upgrade\.db-wal') "installer.iss missing WAL pre-upgrade backup"
Assert-True ($iss -match 'PRIVACY\.md') "installer.iss missing PRIVACY.md"
Assert-True ($iss -match 'SECURITY\.md') "installer.iss missing SECURITY.md"
Assert-True ($iss -match 'updates\\latest\.json' -or $iss -match 'updates/latest\.json') "installer.iss must pack updates/latest.json"

# --- Signing readiness
Assert-True (Test-Path "scripts/AuthenticodeSigning.ps1") "Missing AuthenticodeSigning.ps1"
Assert-True (Test-Path "scripts/sign_authenticode.ps1") "Missing sign_authenticode.ps1"
Assert-True (Test-Path "scripts/verify_release_signatures.ps1") "Missing verify_release_signatures.ps1"
Assert-True (Test-Path "docs/SIGNING.md") "Missing docs/SIGNING.md"
$build = Get-Content "scripts/build_release.ps1" -Raw
Assert-True ($build -match 'Invoke-AuthenticodeSign') "build_release.ps1 missing Invoke-AuthenticodeSign"
Assert-True ($build -match 'Sign-Installer') "build_release.ps1 missing Sign-Installer"
Assert-True ($build -match 'Create-Checksum') "build_release.ps1 missing Create-Checksum"
Assert-True ($build -match 'Find-CodeSigningCertificate') "build_release.ps1 missing Find-CodeSigningCertificate"
Assert-True ($build -match 'verify_release_signatures\.ps1') "build_release.ps1 missing verify_release_signatures.ps1"

# --- Update channel readiness
Assert-True (Test-Path "updates/latest.json") "Missing updates/latest.json"
Assert-True (Test-Path "resources/update_keys/production/manifest_hmac.hex") "Missing production update HMAC key"
Assert-True (Test-Path "scripts/sign_update_manifest.ps1") "Missing sign_update_manifest.ps1"
Assert-True (Test-Path "app/core/update.py") "Missing app/core/update.py"

$manifest = Get-Content "updates/latest.json" -Raw | ConvertFrom-Json
Assert-True (-not [string]::IsNullOrWhiteSpace([string]$manifest.version)) "latest.json missing version"
$url = [string]$manifest.url
if ($url) {
    Assert-True ($url.ToLower().StartsWith("https://")) "latest.json url must be HTTPS when set"
    $sha = [string]$manifest.sha256
    Assert-True ($sha -match '^[0-9a-fA-F]{64}$') "latest.json with url requires sha256 (64 hex)"
    if ($RequireUpdateSignature) {
        Assert-True (-not [string]::IsNullOrWhiteSpace([string]$manifest.signature)) "latest.json missing signature (-RequireUpdateSignature)"
    }
}

# --- License / commercial docs
Assert-True (Test-Path "docs/SECURITY.md") "Missing docs/SECURITY.md"
Assert-True (Test-Path "app/services/licensing_service.py") "Missing licensing_service.py"
Assert-True (Test-Path "app/services/license_gate.py") "Missing license_gate.py"

# --- Version sync smoke
$py = @"
from pathlib import Path
from app.core.constants import APP_VERSION, APP_CHANNEL, SCHEMA_VERSION
vt = Path('Version.txt').read_text(encoding='utf-8')
assert f'Version: {APP_VERSION} {APP_CHANNEL}' in vt
iss = Path('packaging/version.iss').read_text(encoding='utf-8')
assert f'MyAppVersion \"{APP_VERSION}\"' in iss
assert f'MySchemaVersion \"{SCHEMA_VERSION}\"' in iss
print('version sync OK', APP_VERSION, APP_CHANNEL, 'SCHEMA', SCHEMA_VERSION)
"@
python -c $py
if ($LASTEXITCODE -ne 0) {
    [void]$failures.Add("Version sync check failed")
}

# --- Optional post-build Authenticode
if ($RequireSignedArtifacts) {
    & "$PSScriptRoot\verify_release_signatures.ps1" -RequireSigned
    if ($LASTEXITCODE -ne 0) {
        [void]$failures.Add("Authenticode verification failed")
    }
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "FAILED ($($failures.Count)):" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "GOLD-4 installer production checks: PASSED" -ForegroundColor Green
exit 0
