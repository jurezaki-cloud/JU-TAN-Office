#Requires -Version 5.1
<#
.SYNOPSIS
  Shared Authenticode helpers for JU-TAN Office release scripts.

.DESCRIPTION
  Dot-source from build_release.ps1 / build_portable.ps1 / sign_authenticode.ps1.
  Certificate is NEVER required unless -Required is passed to Invoke-AuthenticodeSign
  (or JU_TAN_REQUIRE_SIGNED=1 via Test-JuTanRequireSigned).

.ENVIRONMENT
  JU_TAN_PFX            Path to code-signing PFX
  JU_TAN_PFX_PASSWORD   PFX password (may be empty)
  JU_TAN_TIMESTAMP_URL  RFC 3161 timestamp URL (default: DigiCert)
  JU_TAN_SIGNTOOL       Optional full path to signtool.exe
  JU_TAN_REQUIRE_SIGNED When "1"/"true"/"yes", release mode requires signatures
#>

function Test-JuTanRequireSigned {
    param([switch]$RequiredSwitch)
    if ($RequiredSwitch) { return $true }
    $flag = [string]$env:JU_TAN_REQUIRE_SIGNED
    return ($flag -eq "1" -or $flag -eq "true" -or $flag -eq "TRUE" -or $flag -eq "yes")
}

function Get-JuTanTimestampUrl {
    if ($env:JU_TAN_TIMESTAMP_URL -and $env:JU_TAN_TIMESTAMP_URL.Trim()) {
        return $env:JU_TAN_TIMESTAMP_URL.Trim()
    }
    return "http://timestamp.digicert.com"
}

function Find-SignTool {
    <#
    .SYNOPSIS
      Locate signtool.exe from Windows SDK installs (preferred architecture first).
    #>
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($env:JU_TAN_SIGNTOOL -and (Test-Path -LiteralPath $env:JU_TAN_SIGNTOOL)) {
        return (Resolve-Path -LiteralPath $env:JU_TAN_SIGNTOOL).Path
    }

    $kitRoots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin",
        "${env:ProgramFiles(x86)}\Windows Kits\11\bin",
        "${env:ProgramFiles}\Windows Kits\11\bin"
    )

    foreach ($root in $kitRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        $versionDirs = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^\d+\.' } |
            Sort-Object { try { [version]$_.Name } catch { [version]"0.0" } } -Descending
        foreach ($ver in $versionDirs) {
            foreach ($arch in @("x64", "arm64", "x86")) {
                $p = Join-Path $ver.FullName "$arch\signtool.exe"
                if (Test-Path -LiteralPath $p) { [void]$candidates.Add($p) }
            }
        }
        foreach ($arch in @("x64", "arm64", "x86")) {
            $p = Join-Path $root "$arch\signtool.exe"
            if (Test-Path -LiteralPath $p) { [void]$candidates.Add($p) }
        }
    }

    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { [void]$candidates.Add($cmd.Source) }

    if ($candidates.Count -gt 0) { return $candidates[0] }
    return $null
}

function Test-JuTanSigningReady {
    <#
    .SYNOPSIS
      Returns a hashtable: Ready, Reason, SignTool, PfxPath, TimestampUrl
    #>
    $ts = Get-JuTanTimestampUrl
    $tool = Find-SignTool
    $pfx = $env:JU_TAN_PFX

    if (-not $pfx -or -not $pfx.Trim()) {
        return @{
            Ready        = $false
            Reason       = "JU_TAN_PFX is not set. Unsigned build is OK for development/RC. See docs/SIGNING.md."
            SignTool     = $tool
            PfxPath      = $null
            TimestampUrl = $ts
        }
    }
    if (-not (Test-Path -LiteralPath $pfx)) {
        return @{
            Ready        = $false
            Reason       = "JU_TAN_PFX points to a missing file: $pfx"
            SignTool     = $tool
            PfxPath      = $pfx
            TimestampUrl = $ts
        }
    }
    if (-not $tool) {
        return @{
            Ready        = $false
            Reason       = "signtool.exe not found. Install Windows SDK Signing Tools, or set JU_TAN_SIGNTOOL. See docs/SIGNING.md."
            SignTool     = $null
            PfxPath      = $pfx
            TimestampUrl = $ts
        }
    }
    return @{
        Ready        = $true
        Reason       = "ok"
        SignTool     = $tool
        PfxPath      = (Resolve-Path -LiteralPath $pfx).Path
        TimestampUrl = $ts
    }
}

function Invoke-AuthenticodeSign {
    <#
    .SYNOPSIS
      Sign a single binary. Skips when certificate is absent unless -Required.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$Required
    )

    $must = Test-JuTanRequireSigned -RequiredSwitch:$Required

    if (-not (Test-Path -LiteralPath $Path)) {
        $msg = "Cannot sign — file not found: $Path"
        if ($must) { throw $msg }
        Write-Host $msg
        return $false
    }

    $ready = Test-JuTanSigningReady
    if (-not $ready.Ready) {
        if ($must) {
            throw "Authenticode required but signing is not ready: $($ready.Reason)"
        }
        Write-Host "Unsigned (OK for development/RC): $Path — $($ready.Reason)"
        return $false
    }

    $password = if ($null -ne $env:JU_TAN_PFX_PASSWORD) { $env:JU_TAN_PFX_PASSWORD } else { "" }
    $signArgs = @(
        "sign",
        "/fd", "SHA256",
        "/td", "SHA256",
        "/tr", $ready.TimestampUrl,
        "/f", $ready.PfxPath
    )
    if ($password -ne "") {
        $signArgs += @("/p", $password)
    }
    $signArgs += $Path

    Write-Host "Signing: $Path"
    Write-Host "  signtool: $($ready.SignTool)"
    Write-Host "  timestamp: $($ready.TimestampUrl)"

    & $ready.SignTool @signArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Authenticode signing failed for $Path (signtool exit $LASTEXITCODE). Check PFX password, cert validity, and network access to the timestamp server."
    }
    Write-Host "Signed: $Path"
    return $true
}
