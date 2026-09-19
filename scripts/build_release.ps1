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
New-Item -ItemType Directory -Force -Path "$portable/config" | Out-Null
Copy-Item "config/app.example.json" "$portable/config/app.example.json" -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "dist" | Out-Null
if (Test-Path "dist/JU-TAN-Office-Portable.zip") { Remove-Item "dist/JU-TAN-Office-Portable.zip" -Force }
Compress-Archive -Path $portable -DestinationPath "dist/JU-TAN-Office-Portable.zip"
Write-Host "Portable ZIP: dist/JU-TAN-Office-Portable.zip"

Copy-Item "packaging/Version.txt" "dist/Version.txt" -Force
Copy-Item "LICENSE.txt" "dist/LICENSE.txt" -Force
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
$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "packaging/installer.iss"
    $setup = "dist/JU-TAN-Office-Setup.exe"
    Copy-Item "packaging/Version.txt" "dist/Version.txt" -Force
    Copy-Item "docs/RELEASE_NOTES.md" "dist/RELEASE_NOTES.md" -Force -ErrorAction SilentlyContinue
    if ($env:JU_TAN_PFX -and (Test-Path $env:JU_TAN_PFX) -and (Test-Path $setup)) {
        $signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\x64\signtool.exe"
        if (Test-Path $signtool) {
            & $signtool sign /fd SHA256 /f $env:JU_TAN_PFX /p $env:JU_TAN_PFX_PASSWORD /tr http://timestamp.digicert.com /td SHA256 $setup
            Write-Host "Podpisan installer: $setup"
        } else {
            Write-Host "signtool ni na voljo — Setup.exe ni podpisan."
        }
    } else {
        Write-Host "Certifikat JU_TAN_PFX ni nastavljen — Setup.exe ni podpisan."
    }
    Write-Host "Installer: $setup"
} else {
    Write-Host "Inno Setup ni nameščen — preskočen installer. Portable mapa je v dist/JU-TAN-Office-Portable"
}
Write-Checksums
