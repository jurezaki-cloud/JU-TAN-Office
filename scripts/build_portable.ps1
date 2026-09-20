$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean packaging/ju-tan-office.spec

$portable = "dist/JU-TAN-Office-Portable"
if (Test-Path $portable) { Remove-Item $portable -Recurse -Force }
Copy-Item "dist/JU-TAN-Office" $portable -Recurse
New-Item -ItemType Directory -Force -Path "$portable/data","$portable/exports","$portable/logs","$portable/Backup","$portable/Temp","$portable/Reports" | Out-Null
Copy-Item "packaging/Version.txt" "$portable/Version.txt" -Force
Copy-Item "packaging/LICENSE.txt" "$portable/LICENSE.txt" -Force
Copy-Item "config/app.example.json" "$portable/config/app.example.json" -Force -ErrorAction SilentlyContinue
Write-Host "Portable build: $portable"
