# TASK-029 — Enterprise Release Candidate (RC1)

Datum: 2026-09-12  
Različica: **1.0.0-rc1**  
Pravilo: **code freeze** — ni novih modulov, tabel ali poslovne logike.

## Tokeni

| Token | Stanje |
| --- | --- |
| RC_READY | DA |
| QA_PASS | DA (pytest) |
| PERFORMANCE_PASS | DA (100k seznam < 50 ms stran, iskanje < 250 ms; init baze < 8 s na tem stroju) |
| DATABASE_PASS | DA (FK, UNIQUE, NOT NULL, CASCADE/RESTRICT, indeksi, rollback, integrity_check) |
| SECURITY_PASS | DA (parametriziran SQL, whitelist identifikatorjev, permissions+audit, path traversal, WAL backup) |
| INSTALLER_READY | DA (spec + Inno: ikona, version info, Start Menu, namizje, uninstaller) |
| RELEASE_READY | DA za notranji RC1; produkcija 1.0.0 po podpisu installerja in preizkusu na kopiji podatkov |

## QA moduli

| Modul | Login | CRUD / iskanje | Print/PDF/Excel | Opomba |
| --- | --- | --- | --- | --- |
| Login | n/a | n/a | n/a | Lokalna enouporabniška app, brez zaslona za prijavo |
| Dashboard | — | branje | — | Vedno naložen |
| Customers | — | Create/Read/Update/Delete/Search | Excel | Testi + UI smoke |
| Suppliers | — | CRUD + filter | — | Integracija nabave |
| Products (Artikli) | — | CRUD + unique koda | Excel | Unit |
| Quotes (Ponudbe) | — | CRUD | PDF/Excel | UI okvir |
| Orders | — | CRUD | PDF | Shema + indeksi |
| Invoices | — | CRUD | PDF/Excel | FK restrict/cascade |
| Inventory | — | gibanja | Excel/Print | `warehouse.json` |
| Purchase | — | tok naročila | PDF/Excel | Integracija |
| CRM | — | lead/aktivnost | Excel | Integracija |
| DMS | — | mapa/datoteka | seznam Excel | Integracija |
| Reports | — | filtri | PDF/Excel/CSV/Print | Integracija |
| Analytics | — | branje | — | Deloma vzorčni grafikoni |
| Settings | — | shranjevanje | backup/restore | Atomski JSON + DB backup |
| Automation | — | pravila | Excel | Testi engine |

## Performanse (offscreen / pytest)

- Inicializacija SQLite: < 2 s
- Paginacija 100 000 vrstic: < 50 ms
- Linearno iskanje 100 000: < 250 ms
- Lazy strani: moduli se naložijo ob prvem obisku
- Čas prijave: n/a (ni logina)
- Čas zagona UI: odvisen od stroja; High DPI PassThrough, WAL

## Baza

- `PRAGMA foreign_keys=ON`, WAL, `busy_timeout=5000` (zaklep zapisov v SQLite)
- UNIQUE: številke računov/ponudb/naročil
- NOT NULL: npr. `customers.company`, `articles.name`
- CASCADE: postavke dokumentov; RESTRICT: stranka z dokumenti
- Indeksi na iskalnih in FK stolpcih (`CREATE INDEX IF NOT EXISTS`)
- `Database.transaction()` z rollback

## Varnost

- Parametriziran SQL + `_ident` whitelist
- `permissions.can/require` + `AUDIT` v dnevnik
- Backup/restore zahtevata `backup` permission
- Validacije `app.core.security`
- Ni večuporabniškega RBAC / šifriranja baze (znana omejitev v1.0)

## Pakiranje

- `packaging/ju-tan-office.spec` — ikona, `file_version_info.txt`
- `packaging/installer.iss` — desktop, Start Menu, Odstrani, VersionInfo
- `scripts/build_release.ps1` — PyInstaller + Inno Setup 6
- Ikona: `resources/app.ico`

## Testi

Glej izhod pytest: **43 passed** (brez UI smoke v istem procesu); UI smoke **3 passed** ločeno. Znana omejitev: Qt offscreen se ob uničenju `MainWindow` včasih sesuje, če so v istem procesu že bili drugi dialogi.

## Odprti TODO (po 1.0.0)

- Authenticode podpis installerja
- Polni RBAC in prijava, če bo več uporabnikov
- Odprava vzorčnih podatkov v analitiki
- Poročilo Service
- CI (GitHub Actions)
