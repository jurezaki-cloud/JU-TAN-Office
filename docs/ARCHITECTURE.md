# Arhitektura — JU-TAN Office Enterprise

Aplikacija je **lokalna namizna** PySide6 rešitev. Ni HTTP API strežnika.

## Sklad

| Plast | Lokacija | Vloga |
| --- | --- | --- |
| Vstop | `app.py` | Log, inicializacija SQLite, `run()` |
| Okno | `app/windows/main_window.py` | Sidebar, toolbar, `QStackedWidget` (fiksni indeksi 0–15) |
| Moduli | `app/modules/*` | Strani, dialogi, controllerji, storitve |
| Widgeti | `app/widgets/*` | Tabele (`EnterpriseTable`), KPI, navigacija |
| Podatki | `app/database/*` | SQLite + repository |
| Dokumenti | `app/pdf/*`, `app/excel/*` | Izvoz PDF/XLSX |
| Jedro | `app/core/*` | Konstante, log, napake, cache, lazy strani, varnost |
| Tema | `app/theme/` | QSS + `ThemeManager` (brez lokalnih stylesheetov) |

## Diagram modulov

```mermaid
flowchart TB
  subgraph shell [Lupina]
    MW[MainWindow]
    SB[ModernSidebar]
    TB[ModernToolbar]
    ST[QStackedWidget]
    MW --> SB
    MW --> TB
    MW --> ST
  end
  subgraph pages [Strani - indeksi]
    D[0 Dashboard]
    I[1 Računi]
    C[2 Stranke]
    O[3 Ponudbe]
    A[4 Artikli]
    CO[5 Podjetje]
    P[6 Plačila]
    AN[7 Analitika]
    SE[8 Nastavitve]
    OR[9 Naročila]
    W[10 Skladišče]
    SU[11 Dobavitelji]
    PU[12 Nabava]
    DO[13 DMS]
    CR[14 CRM]
    RE[15 Poročila]
    AU[16 Automation]
  end
  ST --> D
  ST --> I
  ST --> C
  ST --> O
  ST --> A
  ST --> CO
  ST --> P
  ST --> AN
  ST --> SE
  ST --> OR
  ST --> W
  ST --> SU
  ST --> PU
  ST --> DO
  ST --> CR
  ST --> RE
  ST --> AU
  subgraph data [Persistenca]
    SQLITE[(ju_tan.db)]
    JSON[settings.json / warehouse.json]
    FILES[data/documents]
  end
  I --> SQLITE
  C --> SQLITE
  CR --> SQLITE
  W --> JSON
  DO --> FILES
```

## Performanse

- Strani 1–15 so `LazyPage` (tovarna ob prvem obisku; indeksi ostanejo).
- Poročila: `QTimer` + `QThread` + paginacija 50 vrstic.
- SQLite: WAL, `busy_timeout`, parametri `?`.
- `ttl_cache` na `ReportingService.filter_options`.

## Varnost

- Parametrizirani SQL, whitelist identifikatorjev v `BaseRepository`.
- Atomski zapis nastavitev, obnovitev poškodovanega JSON.
- Dovoljenja: lokalni enouporabniški model + audit log.
- Poti: `ensure_inside`, `safe_filename`.
