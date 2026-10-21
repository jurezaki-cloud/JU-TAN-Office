# Skrbniški vodič — JU-TAN Office Enterprise 1.0.8 GOLD

## Namestitev

Privzeto: `C:\Program Files\JU-TAN Office\`  
Podatki: `%ProgramData%\JU-TAN Office\` (Data, Logs, Backup, Temp, Reports).

Uninstall ne zbriše baze, backupov in dokumentov.

## Shema baze

SQLite 3, WAL, tuji ključi, `SCHEMA_VERSION = 3`. Nadgradnja z 1.0.7 ohrani obstoječe podatke: CloseApplications/AppMutex, nato WAL-varna kopija v `pre-upgrade.db` (+ sidecars). Shema se v 1.0.8 ne zviša.

Obnova baze v Nastavitvah je dovoljena samo aktivnemu skrbniku iz tabele `users` in zahteva njegovo geslo. Vloga v odprti seji sama po sebi ni dovolj.

Če je `setup_complete`, a tabela `users` prazna (legacy), zagon odpre **Nastavitev prijave** in ustvari prvega skrbnika — brez ponovnega čarovnika in brez brisanja poslovnih podatkov.

## Vloge (RBAC)

Administrator, Manager, Sales, Warehouse, Accounting, Read Only.

## Gesla in skrivnosti

Gesla so hashirana (Argon2id ali scrypt). SMTP/API/licence so v `secrets_blob`.

## Dnevniki

`Logs/app.log` — rotacija, gzip, čiščenje. Audit: `audit.jsonl` in tabela `audit_log`.

## Obnovitev po sesutju

WAL + `crash.flag` + osnutki v `drafts/`. Integrity check ob zagonu.

## Izgradnja

```powershell
# RC / notranji build (brez certifikata):
.\scripts\build_release.ps1

# Podpisan produkcijski release (Cert:\CurrentUser\My, CN=JU-TAN Studio):
.\scripts\build_release.ps1 -RequireSigned
.\scripts\verify_release_signatures.ps1 -RequireSigned

# Alternativa (CI / migracija): PFX
# $env:JU_TAN_PFX = "C:\certs\ju-tan.pfx"
# $env:JU_TAN_PFX_PASSWORD = "***"
```

Vrstni red: build → podpis EXE → installer → podpis Setup → `signtool verify` → `dist/SHA256SUMS.txt`. Glej `docs/SIGNING.md`. Oznaka git: `v1.0.0`.

## Zasebnost

Politika zasebnosti: `docs/PRIVACY.md` (tudi v Namestitvenem meniju in Nastavitve → Zasebnost).
