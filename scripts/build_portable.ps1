#Requires -Version 5.1
<#
.SYNOPSIS
  Build portable JU-TAN Office tree (no installer).

.DESCRIPTION
  Signs JU-TAN-Office.exe after PyInstaller when JU_TAN_PFX is set.
  Does not require a certificate for development builds.
#>
[CmdletBinding()]
param(
    [switch]$RequireSigned
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

. "$PSScriptRoot\AuthenticodeSigning.ps1"
$require = Test-JuTanRequireSigned -RequiredSwitch:$RequireSigned

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean packaging/ju-tan-office.spec

$appExe = "dist/JU-TAN-Office/JU-TAN-Office.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller output missing: $appExe"
}
Invoke-AuthenticodeSign -Path $appExe -Required:$require

$portable = "dist/JU-TAN-Office-Portable"
if (Test-Path $portable) { Remove-Item $portable -Recurse -Force }
Copy-Item "dist/JU-TAN-Office" $portable -Recurse
New-Item -ItemType Directory -Force -Path "$portable/data","$portable/exports","$portable/logs","$portable/Backup","$portable/Temp","$portable/Reports","$portable/docs","$portable/config" | Out-Null
Copy-Item "packaging/Version.txt" "$portable/Version.txt" -Force
Copy-Item "packaging/LICENSE.txt" "$portable/LICENSE.txt" -Force
Copy-Item "docs/PRIVACY.md" "$portable/docs/PRIVACY.md" -Force
Copy-Item "docs/INSTALL.md" "$portable/docs/INSTALL.md" -Force
Copy-Item "docs/USER_GUIDE.md" "$portable/docs/USER_GUIDE.md" -Force
Copy-Item "docs/ADMIN_GUIDE.md" "$portable/docs/ADMIN_GUIDE.md" -Force
Copy-Item "docs/RELEASE_NOTES.md" "$portable/docs/RELEASE_NOTES.md" -Force
Copy-Item "docs/SECURITY.md" "$portable/docs/SECURITY.md" -Force
Copy-Item "docs/SIGNING.md" "$portable/docs/SIGNING.md" -Force -ErrorAction SilentlyContinue
Copy-Item "config/app.example.json" "$portable/config/app.example.json" -Force -ErrorAction SilentlyContinue

$portableExe = "$portable/JU-TAN-Office.exe"
if (Test-Path -LiteralPath $portableExe) {
    $portSig = Get-AuthenticodeSignature -FilePath $portableExe
    if ($portSig.Status -ne "Valid") {
        $ready = Test-JuTanSigningReady
        if ($ready.Ready -or $require) {
            Invoke-AuthenticodeSign -Path $portableExe -Required:$require
        }
    }
}

Write-Host "Portable build: $portable"
