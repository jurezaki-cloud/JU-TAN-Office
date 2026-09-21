#Requires -Version 5.1
<#
.SYNOPSIS
  Verify Authenticode signatures on JU-TAN Office release binaries.

.DESCRIPTION
  Always reports signature status and publisher for known artifacts.
  Fails the process only when -RequireSigned is set, or JU_TAN_REQUIRE_SIGNED=1.
  Development / RC verification without -RequireSigned never fails on unsigned files.

.PARAMETER DistRoot
  Folder containing release outputs (default: dist relative to repo root).

.PARAMETER RequireSigned
  Exit non-zero if any required target is missing a Valid Authenticode signature.
#>
[CmdletBinding()]
param(
    [string]$DistRoot = "",
    [switch]$RequireSigned
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $DistRoot) {
    $DistRoot = Join-Path $repoRoot "dist"
} elseif (-not [System.IO.Path]::IsPathRooted($DistRoot)) {
    $DistRoot = Join-Path $repoRoot $DistRoot
}

. "$PSScriptRoot\AuthenticodeSigning.ps1"

function Get-PublisherDisplay {
    param($Signature)
    if (-not $Signature -or -not $Signature.SignerCertificate) {
        return "(none)"
    }
    $cert = $Signature.SignerCertificate
    $cn = ($cert.Subject -split ",") | Where-Object { $_.Trim().StartsWith("CN=") } | Select-Object -First 1
    if ($cn) { return $cn.Trim().Substring(3) }
    return $cert.Subject
}

# Required for a "signed release": app EXE + Setup when present.
# Portable EXE is verified when the portable tree exists (same binary family).
$targets = @(
    @{ Rel = "JU-TAN-Office\JU-TAN-Office.exe"; Kind = "app"; RequiredIfExists = $true; MustExistForRelease = $true },
    @{ Rel = "JU-TAN-Office-Setup.exe"; Kind = "setup"; RequiredIfExists = $true; MustExistForRelease = $false },
    @{ Rel = "JU-TAN-Office-Portable\JU-TAN-Office.exe"; Kind = "portable"; RequiredIfExists = $true; MustExistForRelease = $false }
)

$must = Test-JuTanRequireSigned -RequiredSwitch:$RequireSigned
$failures = @()
$reported = 0

Write-Host "=== JU-TAN Office Authenticode verification ==="
Write-Host "Dist: $DistRoot"
Write-Host "Mode: $(if ($must) { 'RELEASE (signatures required)' } else { 'advisory (unsigned OK for development/RC)' })"
Write-Host ""

foreach ($t in $targets) {
    $full = Join-Path $DistRoot $t.Rel
    if (-not (Test-Path -LiteralPath $full)) {
        Write-Host "[skip] $($t.Rel) — not present"
        if ($must -and $t.MustExistForRelease) {
            $failures += "Missing required release binary: $($t.Rel)"
        }
        continue
    }

    $sig = Get-AuthenticodeSignature -FilePath $full
    $publisher = Get-PublisherDisplay -Signature $sig
    $status = [string]$sig.Status
    $reported++

    Write-Host ("[{0}] {1}" -f $t.Kind, $t.Rel)
    Write-Host ("  Status:    {0}" -f $status)
    Write-Host ("  Publisher: {0}" -f $publisher)
    if ($sig.SignerCertificate) {
        Write-Host ("  Subject:   {0}" -f $sig.SignerCertificate.Subject)
        Write-Host ("  Thumbprint:{0}" -f $sig.SignerCertificate.Thumbprint)
        if ($sig.SignerCertificate.NotAfter) {
            Write-Host ("  ValidTo:   {0:u}" -f $sig.SignerCertificate.NotAfter)
        }
    }
    if ($sig.StatusMessage) {
        Write-Host ("  Message:   {0}" -f $sig.StatusMessage)
    }
    Write-Host ""

    if ($must -and $t.RequiredIfExists -and $status -ne "Valid") {
        $failures += "Invalid or missing Authenticode signature on $($t.Rel) (Status=$status, Publisher=$publisher)"
    }
}

if ($reported -eq 0) {
    $msg = "No release binaries found under $DistRoot. Build first (scripts/build_release.ps1)."
    if ($must) {
        $failures += $msg
    } else {
        Write-Host $msg
    }
}

if ($failures.Count -gt 0) {
    Write-Host "RELEASE VERIFICATION FAILED:" -ForegroundColor Red
    foreach ($f in $failures) {
        Write-Host "  - $f" -ForegroundColor Red
    }
    Write-Host "See docs/SIGNING.md for certificate setup and build order."
    exit 1
}

Write-Host "Verification complete ($(if ($must) { 'all required signatures Valid' } else { 'advisory — no hard failures' }))."
exit 0
