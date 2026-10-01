# Namestitev — JU-TAN Office Enterprise 1.0.3 GOLD

## Namestitveni paket

`dist/JU-TAN-Office-Setup.exe` (64-bit, Inno Setup).

```powershell
# Razvoj / RC (certifikat ni potreben):
.\scripts\build_release.ps1

# Produkcijski podpisani release (Cert:\CurrentUser\My CN=JU-TAN Studio, ali JU_TAN_PFX):
# .\scripts\build_release.ps1 -RequireSigned
```

Podrobnosti: `docs/SIGNING.md`.

Privzeta mapa: `C:\Program Files\JU-TAN Office\`  
Podatki: `%ProgramData%\JU-TAN Office\` (Data, Logs, Backup, Temp, Reports).  
Aktivacija naprave: `%LocalAppData%\JU-TAN\Office\` (ločeno od poslovnih podatkov).

Bližnjice: namizje (opcijsko), Start meni, Programs, Odstrani.

## Načini namestitve

- **Prva namestitev** (ni starih podatkov): običajna namestitev, prazen poslovni prostor.
- **Nadgradi / ponovno namesti in ohrani podatke**: privzeto, ko Setup najde obstoječe podatke. Poslovni podatki ostanejo.
- **Nova čista namestitev**: samo po izrecni izbiri in potrditvi. Priporočena varnostna kopija pred izbrisom. Program se inicializira brez podjetij, strank, artiklov, računov, …

Tiha namestitev (`/SILENT`) **vedno ohrani** podatke (nikoli samodejna čista namestitev).

## Odstranitev

1. **Odstrani program** — program se odstrani; poslovni podatki ostanejo.
2. **Popolnoma odstrani … in vse podatke** — po potrditvi; varnostne kopije le, če to izrecno označite.

Glej tudi `docs/DATA_LOCATIONS.md`.

## Predpogoji

| Zahteva | Stanje |
| --- | --- |
| Windows 10/11 64-bit | obvezno |
| Disk ~200 MB | preveri installer |
| SQLite | vgrajen |
| .NET Runtime | **ni potreben** |
| SQL Server | **ni potreben** |
| VC++ Runtime | običajno v paketu PyInstaller |
| Podpisan Setup | opcijsko (certifikat `CN=JU-TAN Studio` ali `JU_TAN_PFX`); obvezno le z `-RequireSigned` |

## Prvi zagon

Po čisti namestitvi: licenca / aktivacija → prijava / začetni račun → čarovnik prvega zagona → vnos podjetja → nastavitve → pripravljen za uporabo.

Čarovnik **ne** predizpolni fiktivnih poslovnih podatkov. Produkcijski paket **ne** vsebuje razvojne / demo baze.

## Nadgradnja

Namestite novi Setup.exe in izberite **Nadgradi / ponovno namesti in ohrani podatke** (privzeto). Installer zapre tekočo aplikacijo (`CloseApplications` / `AppMutex`), nato naredi varnostno kopijo baze v `Backup\pre-upgrade.db*`. Ob napaki sheme aplikacija naredi rollback.

**Nadgradnja 1.0.3 → 1.0.4 ne briše** podjetij, strank, artiklov, računov.

Če je bila namestitev označena kot dokončana (`setup_complete`), a še ni uporabnikov v bazi (starejše različice), aplikacija odpre **Nastavitev prijave** — poslovni podatki ostanejo nedotaknjeni.

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

1. Čista namestitev na svež Windows — prazen poslovni prostor (0 podjetij z imenom, 0 strank, 0 artiklov, 0 računov).
2. Nadgradnja z ohranitvijo podatkov — vsi poslovni zapisi ostanejo.
3. Standardna odstranitev → ponovna namestitev — podatki se vrnejo.
4. Popolna odstranitev (z potrditvijo) → ponovna namestitev — svež prazen prostor.
5. Čista namestitev z varnostno kopijo — baza prazna, kopija obstaja.
6. Prvi zagon: čarovnik → ročno podjetje → stranka → artikel → račun → restart → podatki ostanejo.

**Ne** uporabljajte produkcijske baze za uničujoče teste.

## Portable

```powershell
.\scripts\build_portable.ps1
```
