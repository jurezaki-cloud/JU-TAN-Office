# Changelog

## 1.0.7 GOLD — 2026-10-02

- Dashboard 2.0: Center pozornosti prikazuje zapadle terjatve z dejanskim odprtim zneskom po delnih plačilih in račune, ki zapadejo v naslednjih 7 dneh.
- Payment Center 2.0: pregled terjatev po stopnji opomina ter izboljšana podpora delnim plačilom in obljubljenim plačilom.
- Uvoz banke: CSV uvoz, predlog ujemanja po številki računa in znesku ter potrjeno knjiženje visoko zanesljivih ujemanj.
- JU-TAN AI 2.0: nova vprašanja o zapadlih terjatvah z računom, stranko, rokom in dejanskim preostankom.
- Premium dokumenti: izboljšan footer in diskretne A4 oznake za pregib na 99 mm in 198 mm.

## 1.0.6 GOLD — 2026-10-01

- Nabava: dodan popust na posamezno postavko in pravilni preračun osnove, DDV ter skupnega zneska.
- Baza: glavna inicializacija ob zagonu zdaj samodejno izvede migracijo modula Nabava in doda manjkajoči stolpec `discount` tudi pri nadgradnji stare baze.
- Dodan regresijski test za nadgradnjo obstoječe baze brez stolpca `discount`.
- Release paket ostaja združljiv z varno nadgradnjo, ki ohrani poslovne podatke in lokalno aktivacijo licence.

## 1.0.5 — razvoj

- Začetek novega Command Centra z akcijskimi opozorili za zapadle račune in CRM naloge.
- Opozorila ločijo zapadle naloge, današnje naloge in obveznosti v naslednjih 7 dneh.
- Razvoj poteka na ločeni veji `feature/office-1.0.5`; 1.0.4 ostaja nespremenjena produkcijska osnova.

## 1.0.4 GOLD — 2026-10-01

- Stabilizirana lokalna aktivacija licence: ponovni zagon ali prijava ne odstrani veljavne aktivacije.
- Izboljšan vnos delnega plačila računa in prikaz zneska v EUR.
- Izboljšave prijave/odklepa po neaktivnosti ter dashboarda.
## 1.0.3 GOLD — 2026-09-28

- Dokumentni urejevalnik: vidni primarni gumb »Dodaj postavko«, prazen stan postavk, usklajene kartice in tipografija.
- PDF: poravnane ikone kontakta, odstranjeni odvečni zeleni poudarki pri stranki, podpis »Tanja Hrup«, premaknjen blok Podatki za plačilo.
- Temni način in hierarhija gumbov (Primary / Secondary / Danger) utrjena za urednike dokumentov.
- Namestitev / odstranitev: nadgradnja ohrani podatke; izrecna čista namestitev; standardna vs. popolna odstranitev z varnostnimi kopijami in ohranitvijo aktivacije naprave (`docs/DATA_LOCATIONS.md`).

## 1.0.2 GOLD — 2026-09-28

- Ponudbe uporabljajo blok s podpisom direktorja, enako kot računi.
- Podpis direktorja ostane na računu tudi, kadar podatki za UPN QR niso veljavni.
- UPN QR na računih ostaja vezan na veljavne plačilne podatke; sliko lastnoročnega podpisa je treba nastaviti posebej.

## 1.0.1 GOLD — 2026-09-28

- Popravljen uvoz pogleda Stranke pri prvem odpiranju modula v nameščeni aplikaciji.
- Posodobljeni metapodatki programa in namestitvenega paketa. Shema baze ostaja 3.

## 1.0.0 GOLD — 2026-09-12 (production hardening through 2026-09-19)

Uradna produkcijska izdaja JU-TAN Office Enterprise. `APP_VERSION` = **1.0.0** / kanal **GOLD**.

### Produkcijska utrjanje

- GOLD-1: schema v3 company branding migration; atomic invoice numbering; transactional offer→invoice conversion; Premium PDF redesign freeze.
- GOLD-2: document create numbering under BEGIN IMMEDIATE (invoice save allocate+insert; offer/order/PO create allocates in the same transaction); concurrent-create regression tests.
- GOLD-3A: invoice/offer/order/PO header+items create in one transaction with pre-commit item validation; rollback tests for item-insert failure; travel-order save validates required fields in-transaction.
- GOLD-4: commercial readiness — license HTTPS/DPAPI/device-bind hardening; signed update-manifest channel readiness; installer production check script (`docs/GOLD4_COMMERCIAL_READINESS.md`).
- Centralized EUR money math (`app/utils/money.py`) for editors, recalculation, PDF.
- Offer → invoice conversion implemented (was placeholder).
- Partial/full payment ledger (`payments` table) with Delno plačan / Plačan sync.
- Real UPN QR on invoice PDFs when IBAN + amount are present.
- Removed mock analytics/dashboard chart samples; empty states instead.
- Settings restore/import/export show real errors (no “coming soon” on failure).
- Slovenian navigation/toolbar labels; dashboard unpaid/overdue KPIs.
- RBAC page gating + crash recovery (from security hardening workstream).
- Re-enabled unlock login; settings export strips secrets; role change requires `users`; Read Only cannot open Settings; Excel import reverse-splits VAT; new invoices saved as `Izdan`; PDF export promotes `Osnutek` → `Izdan`.

### Izdaja / paket

- Feature freeze / code freeze, oznaka `v1.0.0`.
- Paket: Setup.exe, Portable ZIP, SHA256 (`dist/SHA256SUMS.txt`), vodiči PDF.
- QA, varnost, zmogljivost in shema baze (`SCHEMA_VERSION` = 3) potrjeni.
- Končni QA Gold: poslovni tok, WAL sočasnost, PDF, stres paginacije (TASK-033).
- Incremental tabele, debounce iskanje, async PDF, Excel streaming.
- Setup.exe 64-bit, čarovnik, licenca, version info, Start Menu / namizje / uninstall.
- Podatki v ProgramData (uninstall jih ohrani).
- Prvi zagon: čarovnik podjetja.
- Nadgradnja: CloseApplications/AppMutex + WAL-varna kopija (`pre-upgrade.db` + sidecars) in rollback ob napaki.
- SQLite vgrajen; .NET in SQL Server nista potrebna.
- Dokumentacija v paketu: PRIVACY, INSTALL, USER_GUIDE, ADMIN_GUIDE, RELEASE_NOTES, SECURITY, SIGNING.

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
- Windows installer Authenticode: pripravljen prek `JU_TAN_PFX` / `-RequireSigned` (glej `docs/SIGNING.md`); razvojni buildi ostanejo nepodpisani.
- PyInstaller/Inno je treba zagnati na build stroju (`scripts/build_release.ps1`).

