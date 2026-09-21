# Varnost — JU-TAN Office Enterprise

Lokalna namizna aplikacija (SQLite). Ni javnega HTTP API.

- Gesla: Argon2id (`argon2-cffi`) ali scrypt + sol; politika min. 10 znakov, velika/mala črka in številka; menjava gesla.
- Skrivnosti (SMTP, API, licenca, connection string): šifriran `secrets_blob` (HMAC + strojni ključ, opcijsko DPAPI).
- RBAC: Administrator, Manager, Sales, Warehouse, Accounting, Read Only — vsaka akcija gre skozi `require` / `gated`; moduli v stranski vrstici so skriti po vlogi.
- Audit: prijava, odjava, zaklep, create/edit/delete, izvoz, tisk — `data/audit.jsonl` + tabela `audit_log`.
- DMS: `ensure_inside`, dovoljene pripone, brez path traversal in sistemskih map.
- SQLite: FK, WAL, `integrity_check`, preverjena varnostna kopija, tedenski VACUUM, rollback po sesutju.
- Dnevniki: velikost, dnevna in tedenska rotacija, gzip, čiščenje starejših od 30 dni.
- Seja: timeout, samodejni zaklep, zapomni uporabnika, varna odjava z geslom.
- Licenca (produkcija): spletna aktivacija + DPAPI žeton + vezava na napravo (`device_id`) + periodična `validate` ob zagonu z offline milostnim rokom. Glej `docs/GOLD4_COMMERCIAL_READINESS.md`.
- Licenca (legacy metadata): lokalni HMAC zapis izdaje/plana v `app.core.license` — **ne** nadomešča spletne aktivacije.
- Konfiguracija: SHA-256 checksum, manjkajoča polja, selitev različice.

`DEBUG` v `app/core/config.py` je `False`. Traceback ostane samo v dnevniku.

Ob zagonu: če obstaja `password_hash`, je zahtevan `UnlockDialog`. Izvoz nastavitev **ne** vključuje `password_hash` / `secrets_blob`. Sprememba vloge zahteva dovoljenje `users` (Administrator).

## Zasebnost

Lokalni model shranjevanja: glej [`PRIVACY.md`](PRIVACY.md). V aplikaciji: Nastavitve → Zasebnost.

**SECURITY_PASSED** (lokalni enouporabniški model; ni formalne pen-test certificiranosti)
