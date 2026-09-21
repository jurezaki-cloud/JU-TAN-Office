#Requires -Version 5.1
<#
.SYNOPSIS
  Shared Authenticode helpers for JU-TAN Office release scripts.

.DESCRIPTION
  Dot-source from build_release.ps1 / build_portable.ps1 / sign_authenticode.ps1.
  Certificate is NEVER required unless -Required is passed to Invoke-AuthenticodeSign
  (or JU_TAN_REQUIRE_SIGNED=1 via Test-JuTanRequireSigned).

  Signing source priority:
    1. Certificate store Cert:\CurrentUser\My with Subject CN=JU-TAN Studio
    2. PFX via JU_TAN_PFX (+ optional JU_TAN_PFX_PASSWORD) — CI / production migration

.ENVIRONMENT
  JU_TAN_PFX            Path to code-signing PFX (fallback)
  JU_TAN_PFX_PASSWORD   PFX password (may be empty)
  JU_TAN_TIMESTAMP_URL  RFC 3161 timestamp URL (default: DigiCert)
  JU_TAN_SIGNTOOL       Optional full path to signtool.exe
  JU_TAN_REQUIRE_SIGNED When "1"/"true"/"yes", release mode requires signatures
  JU_TAN_CERT_SUBJECT   Optional Subject substring (default: CN=JU-TAN Studio)
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

function Get-JuTanCertSubjectNeedle {
    if ($env:JU_TAN_CERT_SUBJECT -and $env:JU_TAN_CERT_SUBJECT.Trim()) {
        return $env:JU_TAN_CERT_SUBJECT.Trim()
    }
    return "CN=JU-TAN Studio"
}

function Find-SignTool {
    <#
    .SYNOPSIS
      Locate newest signtool.exe from Windows SDK installs (x64 preferred).
    #>
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($env:JU_TAN_SIGNTOOL -and (Test-Path -LiteralPath $env:JU_TAN_SIGNTOOL)) {
        return (Resolve-Path -LiteralPath $env:JU_TAN_SIGNTOOL).Path
    }

    # Phase-2 primary search: Windows Kits 10 bin\*\x64\signtool.exe (newest first)
    $kitBinRoots = @(
        "C:\Program Files (x86)\Windows Kits\10\bin",
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin",
        "${env:ProgramFiles(x86)}\Windows Kits\11\bin",
        "${env:ProgramFiles}\Windows Kits\11\bin"
    )

    foreach ($root in $kitBinRoots) {
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

function Find-CodeSigningCertificate {
    <#
    .SYNOPSIS
      Find JU-TAN Studio code-signing cert in Cert:\CurrentUser\My.
    .OUTPUTS
      X509Certificate2 or $null
    #>
    $needle = Get-JuTanCertSubjectNeedle
    $storePath = "Cert:\CurrentUser\My"
    if (-not (Test-Path -LiteralPath $storePath)) {
        return $null
    }

    $matches = Get-ChildItem -LiteralPath $storePath -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Subject -and ($_.Subject -like "*$needle*") -and
            $_.HasPrivateKey -and
            ($_.NotAfter -gt (Get-Date))
        } |
        Sort-Object NotAfter -Descending

    if (-not $matches) { return $null }
    return $matches | Select-Object -First 1
}

function Test-JuTanSigningReady {
    <#
    .SYNOPSIS
      Returns hashtable: Ready, Reason, SignTool, Mode (Store|Pfx), Thumbprint, PfxPath, TimestampUrl
    #>
    $ts = Get-JuTanTimestampUrl
    $tool = Find-SignTool
    $needle = Get-JuTanCertSubjectNeedle

    if (-not $tool) {
        return @{
            Ready        = $false
            Reason       = "signtool.exe not found under 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe'. Install Windows SDK Signing Tools, or set JU_TAN_SIGNTOOL. See docs/SIGNING.md."
            SignTool     = $null
            Mode         = $null
            Thumbprint   = $null
            PfxPath      = $null
            TimestampUrl = $ts
        }
    }

    $cert = Find-CodeSigningCertificate
    if ($cert) {
        return @{
            Ready        = $true
            Reason       = "ok (certificate store)"
            SignTool     = $tool
            Mode         = "Store"
            Thumbprint   = $cert.Thumbprint
            PfxPath      = $null
            TimestampUrl = $ts
            Subject      = $cert.Subject
        }
    }

    $pfx = $env:JU_TAN_PFX
    if ($pfx -and $pfx.Trim()) {
        if (-not (Test-Path -LiteralPath $pfx)) {
            return @{
                Ready        = $false
                Reason       = "JU_TAN_PFX points to a missing file: $pfx"
                SignTool     = $tool
                Mode         = $null
                Thumbprint   = $null
                PfxPath      = $pfx
                TimestampUrl = $ts
            }
        }
        return @{
            Ready        = $true
            Reason       = "ok (PFX fallback)"
            SignTool     = $tool
            Mode         = "Pfx"
            Thumbprint   = $null
            PfxPath      = (Resolve-Path -LiteralPath $pfx).Path
            TimestampUrl = $ts
        }
    }

    return @{
        Ready        = $false
        Reason       = "No code-signing certificate found. Expected Subject containing '$needle' in Cert:\CurrentUser\My, or set JU_TAN_PFX. Unsigned build is OK for development/RC. See docs/SIGNING.md."
        SignTool     = $tool
        Mode         = $null
        Thumbprint   = $null
        PfxPath      = $null
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

    $signArgs = @(
        "sign",
        "/fd", "SHA256",
        "/td", "SHA256",
        "/tr", $ready.TimestampUrl
    )

    if ($ready.Mode -eq "Store") {
        $signArgs += @("/sha1", $ready.Thumbprint)
    }
    else {
        $password = if ($null -ne $env:JU_TAN_PFX_PASSWORD) { $env:JU_TAN_PFX_PASSWORD } else { "" }
        $signArgs += @("/f", $ready.PfxPath)
        if ($password -ne "") {
            $signArgs += @("/p", $password)
        }
    }
    $signArgs += $Path

    Write-Host "Signing: $Path"
    Write-Host "  signtool: $($ready.SignTool)"
    Write-Host "  mode: $($ready.Mode)"
    if ($ready.Thumbprint) {
        Write-Host "  thumbprint: $($ready.Thumbprint)"
    }
    Write-Host "  timestamp: $($ready.TimestampUrl)"

    & $ready.SignTool @signArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Authenticode signing failed for $Path (signtool exit $LASTEXITCODE). Check certificate validity, private key access, and network access to the timestamp server."
    }
    Write-Host "Signed: $Path"
    return $true
}

function Verify-Signature {
    <#
    .SYNOPSIS
      Verify Authenticode with signtool verify /pa /v. Throws on failure when -Required.

    .DESCRIPTION
      Publicly trusted CA signatures must pass /pa. Self-signed CN=JU-TAN Studio
      certificates (Issuer == Subject) are accepted when the signer thumbprint
      matches Find-CodeSigningCertificate, with a clear warning — cryptographic
      integrity is checked via Get-AuthenticodeSignature. Production OV/EV certs
      should pass /pa without this fallback.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$Required
    )

    $must = Test-JuTanRequireSigned -RequiredSwitch:$Required

    if (-not (Test-Path -LiteralPath $Path)) {
        $msg = "Cannot verify — file not found: $Path"
        if ($must) { throw $msg }
        Write-Host $msg
        return $false
    }

    $tool = Find-SignTool
    if (-not $tool) {
        $msg = "signtool.exe not found — cannot verify $Path"
        if ($must) { throw $msg }
        Write-Host $msg
        return $false
    }

    Write-Host "Verifying: $Path"
    & $tool @("verify", "/pa", "/v", $Path)
    $verifyExit = $LASTEXITCODE
    if ($verifyExit -eq 0) {
        Write-Host "Verified: $Path"
        return $true
    }

    # Fallback: self-signed / untrusted root but expected JU-TAN Studio thumbprint
    $sig = Get-AuthenticodeSignature -FilePath $Path
    $expected = Find-CodeSigningCertificate
    $signer = $sig.SignerCertificate
    $thumbOk = $false
    if ($signer -and $expected -and ($signer.Thumbprint -eq $expected.Thumbprint)) {
        $thumbOk = $true
    }
    $selfSigned = $false
    if ($signer -and $signer.Subject -and $signer.Issuer) {
        $selfSigned = ($signer.Subject -eq $signer.Issuer)
    }
    $statusOk = ($sig.Status -eq "Valid" -or $sig.Status -eq "UnknownError" -or $sig.Status -eq "NotTrusted")
    # UnknownError/NotTrusted commonly appear for self-signed; hash must still be present
    $hasSignature = ($null -ne $signer)

    if ($hasSignature -and $thumbOk -and $selfSigned -and $statusOk) {
        Write-Host "WARNING: signtool verify /pa reported untrusted root (exit $verifyExit)." -ForegroundColor Yellow
        Write-Host "  Signature is present and matches Cert:\CurrentUser\My CN=JU-TAN Studio ($($signer.Thumbprint))." -ForegroundColor Yellow
        Write-Host "  Acceptable for internal/self-signed releases. Production requires a publicly trusted OV/EV certificate." -ForegroundColor Yellow
        Write-Host "Verified (self-signed integrity): $Path"
        return $true
    }

    $msg = "Authenticode verification failed for $Path (signtool exit $verifyExit; Status=$($sig.Status))."
    if ($must) { throw $msg }
    Write-Host $msg
    return $false
}
