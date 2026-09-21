# Namestitev — JU-TAN Office Enterprise 1.0.0 GOLD

## Namestitveni paket

`dist/JU-TAN-Office-Setup.exe` (64-bit, Inno Setup).

```powershell
# Razvoj / RC (certifikat ni potreben):
.\scripts\build_release.ps1

# Produkcijski podpisani release (zahteva JU_TAN_PFX + signtool):
# $env:JU_TAN_PFX = "C:\certs\ju-tan.pfx"
# $env:JU_TAN_PFX_PASSWORD = "***"
# .\scripts\build_release.ps1 -RequireSigned
```

Podrobnosti: `docs/SIGNING.md`.

Privzeta mapa: `C:\Program Files\JU-TAN Office\`  
Podatki: `%ProgramData%\JU-TAN Office\` (Data, Logs, Backup, Temp, Reports).

Bližnjice: namizje (opcijsko), Start meni, Programs, Odstrani.

Ob odstranitvi se **ne** zbrišejo baza, backupi in dokumenti.

## Predpogoji

| Zahteva | Stanje |
| --- | --- |
| Windows 10/11 64-bit | obvezno |
| Disk ~200 MB | preveri installer |
| SQLite | vgrajen |
| .NET Runtime | **ni potreben** |
| SQL Server | **ni potreben** |
| VC++ Runtime | običajno v paketu PyInstaller |
| Podpisan Setup | opcijsko (`JU_TAN_PFX`); obvezno le z `-RequireSigned` |

## Prvi zagon

Čarovnik (podjetje, DDV, naslov, davčna št., valuta, logo, administrator) ustvari bazo, privzetega administratorja in nastavitve.

## Nadgradnja

Namestite novi Setup.exe čez obstoječo namestitev. Installer zapre tekočo aplikacijo (`CloseApplications` / `AppMutex`), nato naredi WAL-varno kopijo baze (`ju_tan.db` + morebitna `.db-wal` / `.db-shm`) v `Backup\pre-upgrade.db*`. Ob napaki sheme aplikacija naredi rollback.

Če je bila namestitev označena kot dokončana (`setup_complete`), a še ni uporabnikov v SQLite (starejše različice brez večuporabniške prijave), aplikacija **ne** zažene čarovnika znova. Namesto tega odpre enkratno **Nastavitev prijave** (Credential Onboarding), kjer lastnik ustvari skrbnika. Poslovni podatki ostanejo nedotaknjeni; nato velja običajna prijava.

## Razvoj

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Zasebnost

Politika zasebnosti je vključena v paket (`docs/PRIVACY.md`) in dostopna v Nastavitve → Zasebnost.

## Preizkus namestitve

Ročni kontrolni seznam (po `build_release.ps1`):

1. Čista namestitev na svež Windows 10/11 x64.
2. Prvi zagon — čarovnik, baza in administrator.
3. Nadgradnja z istim Setup.exe (ali višjo verzijo) — `Backup\pre-upgrade.db`.
4. Ponovna namestitev (Repair) brez izgube podatkov.
5. Varnostna kopija in obnovitev v Nastavitvah.
6. Uninstall — program izgine, `%ProgramData%\JU-TAN Office` ostane.

## Portable

```powershell
.\scripts\build_portable.ps1
```
