#Requires -Version 5.1
<#
.SYNOPSIS
  Sign updates/latest.json with HMAC-SHA256 for the commercial update channel.

.DESCRIPTION
  Writes/updates the "signature" field using the key from:
    - JU_TAN_UPDATE_HMAC_KEY (preferred), or
    - resources/update_keys/production/manifest_hmac.hex

  Canonical payload = JSON with sorted keys, no "signature" field.
  Does not change application or accounting logic.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Path = "updates/latest.json"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path -LiteralPath $Path)) {
    throw "Manifest not found: $Path"
}

$keyHex = $env:JU_TAN_UPDATE_HMAC_KEY
if (-not $keyHex -or -not $keyHex.Trim()) {
    $keyFile = "resources/update_keys/production/manifest_hmac.hex"
    if (-not (Test-Path -LiteralPath $keyFile)) {
        throw "Missing JU_TAN_UPDATE_HMAC_KEY and $keyFile"
    }
    $keyHex = (Get-Content -LiteralPath $keyFile -Raw).Trim().Split("`n")[0].Trim()
}
$keyHex = $keyHex.Trim()
if ($keyHex.Length -lt 32) {
    throw "Update HMAC key looks too short."
}

$python = @"
import hashlib, hmac, json, sys
from pathlib import Path

path = Path(sys.argv[1])
key = bytes.fromhex(sys.argv[2])
payload = json.loads(path.read_text(encoding='utf-8'))
if not isinstance(payload, dict):
    raise SystemExit('manifest must be a JSON object')
body = {k: v for k, v in payload.items() if k != 'signature'}
canonical = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
payload['signature'] = hmac.new(key, canonical, hashlib.sha256).hexdigest()
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('Signed', path)
print('signature=', payload['signature'])
"@

python -c $python $Path $keyHex
if ($LASTEXITCODE -ne 0) {
    throw "sign_update_manifest failed (exit $LASTEXITCODE)"
}
