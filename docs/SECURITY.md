# Varnost — JU-TAN Office Enterprise

Lokalna namizna aplikacija (SQLite). Ni javnega HTTP API.

- Gesla: Argon2id (če je `argon2-cffi`) ali scrypt + sol; politika min. 10 znakov.
- Skrivnosti (SMTP, API, licenca, connection string): šifriran `secrets_blob`.
- RBAC: Administrator, Manager, Sales, Warehouse, Accounting, Read Only.
- Audit: `data/audit.jsonl` + tabela `audit_log`.
- DMS: `ensure_inside`, dovoljene pripone, brez path traversal.
- SQLite: FK, WAL, `integrity_check`, preverjena varnostna kopija, občasni VACUUM.
- Dnevniki: rotacija po velikosti in dnevu, gzip, čiščenje.
- Seja: timeout, zaklep, odjava, obnovitev strani po sesutju.
- Licenca: Trial / Professional / Enterprise, offline HMAC.

`DEBUG` v `app/core/config.py` je `False`. Traceback ostane samo v dnevniku.
