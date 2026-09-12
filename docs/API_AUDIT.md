# Revizija API-jev

JU-TAN Office Enterprise **nima omrežnega REST/HTTP API-ja**. Vsa logika teče v procesu namizne aplikacije.

| Površina | Tveganje | Zaščita |
| --- | --- | --- |
| SQLite repository | SQL injekcija | Vezani parametri `?`; identifikatorji whitelist |
| `settings.json` | Poškodovan zapis, path | Atomski write, JSON objekt, obnovitev privzetih |
| DMS datoteke | Path traversal | `safe_filename`, koren `data/documents` |
| Excel/PDF izvoz | Arbitrary path | Uporabnik izbere mapo v nastavitvah |
| Dovoljenja | Večuporabniški dostop | Trenutno en lokalni uporabnik; `permissions.audit` |

Priporočilo za 1.0: ne izpostavljati baze v skupno omrežno mapo brez šifriranja diska.
