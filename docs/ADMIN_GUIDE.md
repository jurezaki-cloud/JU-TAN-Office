# Skrbniški vodič — JU-TAN Office Enterprise 1.0.0 GOLD

## Namestitev

Privzeto: `C:\Program Files\JU-TAN Office\`  
Podatki: `%ProgramData%\JU-TAN Office\` (Data, Logs, Backup, Temp, Reports).

Uninstall ne zbriše baze, backupov in dokumentov.

## Shema baze

SQLite 3, WAL, tuji ključi, `SCHEMA_VERSION = 1`. Nadgradnja naredi `pre-upgrade.db`.

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
.\scripts\build_release.ps1
```

Podpis Setup.exe: nastavite `JU_TAN_PFX`. Oznaka git: `v1.0.0`.
