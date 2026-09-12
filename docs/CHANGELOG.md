# Changelog

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

- Ni ločene prijave (lokalna enouporabniška namizna aplikacija).
- RBAC je revizijski sloj; vse akcije so v v1.0 dovoljene in zabeležene.
- Analitika ima deloma vzorčne grafikone.
- Poročilo **Service** je placeholder.
- Windows installer ni Authenticode podpisan.
- PyInstaller/Inno je treba zagnati na build stroju (`scripts/build_release.ps1`).
