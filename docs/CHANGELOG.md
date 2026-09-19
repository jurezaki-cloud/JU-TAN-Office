# Changelog

## 1.0.1 — production hardening (2026-09-19)

- Centralized EUR money math (`app/utils/money.py`) for editors, recalculation, PDF.
- Offer → invoice conversion implemented (was placeholder).
- Partial/full payment ledger (`payments` table) with Delno plačan / Plačan sync.
- Real UPN QR on invoice PDFs when IBAN + amount are present.
- Removed mock analytics/dashboard chart samples; empty states instead.
- Settings restore/import/export show real errors (no “coming soon” on failure).
- Slovenian navigation/toolbar labels; dashboard unpaid/overdue KPIs.
- RBAC page gating + crash recovery (from security hardening workstream).
- **Follow-up:** re-enabled unlock login; settings export strips secrets; role change requires `users`; Read Only cannot open Settings; Excel import reverse-splits VAT; new invoices saved as `Izdan`; PDF export promotes `Osnutek` → `Izdan`.

## 1.0.0 GOLD — 2026-09-12

Uradna produkcijska izdaja JU-TAN Office Enterprise.

- Feature freeze / code freeze, oznaka `v1.0.0`.
- Paket: Setup.exe, Portable ZIP, SHA256, vodiči PDF.
- QA, varnost, zmogljivost in shema baze (v1) potrjeni.

- Končni QA Gold: poslovni tok, WAL sočasnost, PDF, stres paginacije (TASK-033).
- Incremental tabele, debounce iskanje, async PDF, Excel streaming.

- Setup.exe 64-bit, čarovnik, licenca, version info, Start Menu / namizje / uninstall.
- Podatki v ProgramData (uninstall jih ohrani).
- Prvi zagon: čarovnik podjetja.
- Nadgradnja z backupom baze in rollback ob napaki.
- SQLite vgrajen; .NET in SQL Server nista potrebna.

## 1.0.0-rc1 — 2026-09-12

Kandidatka za izdajo (code freeze, QA, indeksi, dnevniki).


Prva kandidatka za produkcijsko izdajo. **Code freeze:** ni novih modulov, tabel ali sprememb poslovne logike.

### Nova funkcionalnost (v obsegu v1.0, pred zamrznitvijo)

- Moduli: Dashboard, Računi, Stranke, Ponudbe, Artikli, Podjetje, Plačila, Analitika, Nastavitve, Naročila, Skladišče, Dobavitelji, Nabava, DMS, CRM, Poročila, Automation.
- Excel uvoz/izvoz, PDF, responsive dialogi, bližnjice, toasti, statusna vrstica.

### Popravki in stabilnost (TASK-029)

- Indeksi SQLite za iskanje in tujih ključev.
- Varnostna kopija/obnova prek SQLite Backup API (WAL-varno) + `integrity_check`.
- Transakcijski pomočnik z rollback.
- Dnevnik: čas, nivo (ERROR/WARNING/INFO), uporabnik, stack trace.
- Pakiranje: ikona, version info, Start Menu, namizje, odstranjevalnik.

### Znane omejitve

- Ni ločene večuporabniške prijave (lokalna namizna aplikacija z vlogami).
- RBAC je obvezen na zapisu, brisanju, izvozu, tisku in nastavitvah; Read Only vidi module, ne more spreminjati.
- Analitika ima deloma vzorčne grafikone.
- Poročilo **Service** je placeholder.
- Windows installer ni Authenticode podpisan.
- PyInstaller/Inno je treba zagnati na build stroju (`scripts/build_release.ps1`).
