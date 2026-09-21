# Zmogljivost — JU-TAN Office Enterprise

Cilji (lokalna SQLite namizna aplikacija):

| Meritev | Cilj |
| --- | --- |
| Zagon | < 3 s |
| Odpiranje modula (lazy) | < 1 s |
| Iskanje (indeks / FTS / predpomnilnik) | < 300 ms |
| Shranjevanje dokumenta | < 500 ms |
| Predogled tiska (HTML nit) | < 2 s |

## Kaj je vgrajeno

- Splash + profil zagona, ozadno ogrevanje (`openpyxl`, `reportlab`), čiščenje `Temp`.
- Lazy moduli (QStackedWidget indeksi nespremenjeni).
- Dashboard podatki se naložijo po `show` (ne blokirajo prikaza okna po prijavi).
- Kartice / toolbar: QSS elevation brez `QGraphicsDropShadowEffect` (manj flickerja ob navigaciji).
- SQLite: WAL, `cache_size`, `mmap`, `temp_store=MEMORY`, nabor povezav na nit.
- Indeksi + opcijski FTS5 za artikle in stranke.
- Tabele: fiksna višina vrstic, incremental LIMIT/OFFSET (200), debounce iskanja 180 ms.
- Ikone in fonte v predpomnilniku, sličice DMS v `Temp/thumbs`.
- PDF v ozadju, Excel write-only pretok od 400 vrstic, poročila že v QThread.

## Stress (sintetično v testih)

100.000 vrstic `page_slice`, incremental 1.000, SQL `EXPLAIN QUERY PLAN` za indekse.

Dejanski vnos 1.000.000 dokumentov v CI ni vključen (disk). Za ročni test uporabite uvoz Excel.

## Profil

Ob zagonu se v dnevnik zapiše `startup total=…ms` z oznakami `theme`, `splash`, `database`, `auth`, `window`, `shown` in po warmup `memory_mb`.
