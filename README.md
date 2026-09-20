# JU-TAN Office Enterprise

Namizna poslovna aplikacija (PySide6 + SQLite).

**Različica 1.0.0 GOLD** — uradna produkcijska izdaja (2026-09-12).  
Izdajatelj: **JU-TAN Studio**. Copyright © 2026.

## Zahteve

- Windows 10/11
- Python 3.11+ (za razvoj)
- [Namestitev](docs/INSTALL.md)

## Zagon (razvoj)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Testi

```powershell
$env:QT_QPA_PLATFORM="offscreen"
pytest -q
```

## Izgradnja

```powershell
.\scripts\build_release.ps1
```

Portable mapa: `dist/JU-TAN-Office-Portable`  
Installer (če je Inno Setup 6): `dist/JU-TAN-Office-Setup.exe`

## Dokumentacija

- [Namestitev](docs/INSTALL.md)
- [Uporabniški vodič](docs/USER_GUIDE.md) / [PDF](docs/USER_GUIDE.pdf)
- [Skrbniški vodič](docs/ADMIN_GUIDE.md) / [PDF](docs/ADMIN_GUIDE.pdf)
- [Varnost](docs/SECURITY.md)
- [QA Gold](docs/QA_GOLD.md)
- [Changelog](docs/CHANGELOG.md)
- [Release notes](docs/RELEASE_NOTES.md)
- [Licenca](LICENSE.txt)
