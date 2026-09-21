#Requires -Version 5.1
<#
.SYNOPSIS
  Authenticode sign one or more Windows binaries for JU-TAN Office.

.EXAMPLE
  .\scripts\sign_authenticode.ps1 -Path dist\JU-TAN-Office\JU-TAN-Office.exe
  .\scripts\sign_authenticode.ps1 -Path a.exe,b.exe -Required
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string[]]$Path = @(),
    [switch]$Required
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\AuthenticodeSigning.ps1"

if (-not $Path -or $Path.Count -eq 0) {
    Write-Host @"
Usage:
  .\scripts\sign_authenticode.ps1 -Path dist\JU-TAN-Office\JU-TAN-Office.exe
  .\scripts\sign_authenticode.ps1 -Path a.exe,b.exe -Required

Environment: JU_TAN_PFX, JU_TAN_PFX_PASSWORD, JU_TAN_TIMESTAMP_URL, JU_TAN_SIGNTOOL, JU_TAN_REQUIRE_SIGNED
See docs/SIGNING.md
"@
    exit 0
}

$require = Test-JuTanRequireSigned -RequiredSwitch:$Required
$any = $false
foreach ($p in $Path) {
    if (Invoke-AuthenticodeSign -Path $p -Required:$require) { $any = $true }
}
if ($require -and -not $any) {
    throw "No files were signed, but -Required / JU_TAN_REQUIRE_SIGNED was set."
}
