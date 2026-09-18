$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
& ".\.venv\Scripts\pyinstaller.exe" --noconfirm --clean "JU-TAN-Office.spec"

Write-Host "Windows executable created: dist\JU-TAN-Office.exe" -ForegroundColor Green
Write-Host "To create the installer, compile installer\JU-TAN-Office.iss with Inno Setup 6."
