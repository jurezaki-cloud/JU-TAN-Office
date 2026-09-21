# TASK-033 / Release Report — JU-TAN Office Enterprise 1.0.0 GOLD

Datum: 2026-09-21  
Različica: **1.0.0** (`APP_VERSION`) / kanal **GOLD** / `SCHEMA_VERSION` = **3**  
Pravilo: samo pakiranje/dokumentacija/nadgradnja installerja — brez sprememb poslovne logike.

## Tokeni

| Token | Stanje |
| --- | --- |
| RC_READY | DA |
| QA_PASS | DA (pytest release/package suite) |
| PERFORMANCE_PASS | DA (lazy moduli, merjeni budgeti) |
| DATABASE_PASS | DA (FK, UNIQUE, NOT NULL, CASCADE/RESTRICT, indeksi, rollback, integrity_check, SCHEMA 3) |
| SECURITY_PASS | DA (parametriziran SQL, permissions+audit, path traversal, WAL backup, `docs/SECURITY.md` v paketu) |
| INSTALLER_READY | DA (CloseApplications, AppMutex, WAL-varna pre-upgrade kopija, Start Menu docs) |
| RELEASE_READY | DA za 1.0.0 GOLD (Authenticode: opcijsko; obvezno z `-RequireSigned` / `JU_TAN_REQUIRE_SIGNED`) |

## Metapodatki

| Artifact | Vir resnice |
| --- | --- |
| `APP_VERSION` / `APP_CHANNEL` | `app/core/constants.py` → `1.0.0` / `GOLD` |
| `SCHEMA_VERSION` | `app/core/constants.py` → `3` |
| `Version.txt` / `packaging/Version.txt` | `scripts/sync_release_metadata.py` |
| `packaging/version.iss` / `file_version_info.txt` | sync iz `release_meta` |
| Checksums | **samo** `dist/SHA256SUMS.txt` (generira `build_release.ps1`) |

## Dokumentacija v paketu

| Dokument | Installer | PyInstaller datas | Portable |
| --- | --- | --- | --- |
| PRIVACY.md | DA | DA | DA |
| INSTALL.md | DA | DA | DA |
| USER_GUIDE.md | DA | DA | DA |
| ADMIN_GUIDE.md | DA | DA | DA |
| RELEASE_NOTES.md | DA | DA | DA |
| SECURITY.md | DA | DA | DA |
| SIGNING.md | DA | DA | DA |

`INSTALL.md` (root) je usklajen z `docs/INSTALL.md`.

## Nadgradnja (installer)

- `CloseApplications=yes` + `AppMutex=JU-TANOfficeMutex`
- Pred zamenjavo datotek: hladna WAL-varna kopija `ju_tan.db` (+ `.db-wal` / `.db-shm` če obstajata) → `Backup\pre-upgrade.db*`
- ProgramData (Data/Logs/Backup) ostane ob uninstall (`uninsneveruninstall`)

## Pakiranje

- `packaging/ju-tan-office.spec` — ikona, version info, release docs
- `packaging/installer.iss` — desktop, Start Menu (vključno Varnost), Odstrani
- `scripts/build_release.ps1` — PyInstaller → sign EXE → portable → Inno → sign Setup → `dist/SHA256SUMS.txt` → verify
- `scripts/AuthenticodeSigning.ps1` / `sign_authenticode.ps1` / `verify_release_signatures.ps1`
- Ikona: `resources/app.ico`

## Znane omejitve

- Authenticode je pripravljen; brez `JU_TAN_PFX` ostane unsigned (OK za razvoj/RC). Produkcijski gate: `-RequireSigned` (glej `docs/SIGNING.md`).
- Posodobitveni kanal (`updates/latest.json`) je pripravljen; zunanji feed je konfiguracija okolja
