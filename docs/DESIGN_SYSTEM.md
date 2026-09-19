# JU-TAN Design System

Tokenized QSS theme for JU-TAN Office Enterprise (`app/theme/`).

## Tokens

Defined in `app/theme/colors.py`, `app/theme/tokens.py`, injected into `theme.qss` via `ThemeManager`:

| Token | Role |
| --- | --- |
| `PRIMARY` | Brand actions, totals, active nav (default JU-TAN green) |
| `ON_PRIMARY` | Text on primary surfaces |
| `BACKGROUND` | App canvas |
| `SURFACE` / `SURFACE_ELEVATED` | Cards, toolbars, dialogs |
| `BORDER` | Hairline separators |
| `TEXT` / `TEXT_MUTED` | Primary / muted copy |
| `SUCCESS` / `WARNING` / `DANGER` / `INFO` | Status semantics |
| `HOVER` / `SELECTED` / `FOCUS` / `DISABLED` | Interaction states |
| `CARD_RADIUS` / `CONTROL_RADIUS` | Consistent rounding |

Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 (`app/theme/tokens.py`).

## Rules

- No local ad-hoc stylesheets on pages — use object names + global QSS.
- Status meaning must not rely on color alone (badge text required).
- Totals use `#TotalValue` (emphasised primary).
- Default `QPushButton` is secondary; `#PrimaryButton` is the CTA.
- Density: tables 44px row height, controls min 34–36px.
- Charts and KPIs show **real** data only; empty states replace mock samples.
- Icons: coherent stroke set in `app/core/ui/brand_icons.py` (no emoji).

## Shell

- Sidebar: grouped business navigation (`NAV_GROUPS`), icons, collapse, RBAC, scrollable nav with fixed header/footer
- Toolbar: page title + global **+ Novo** menu + lock/settings/user (page search lives on module toolbars)
- Content: stacked lazy pages with consistent ~12–14px workspace margins
- Identity: `resources/app.ico` (JT monogram) via `app_identity`
- Theme: applied at startup from `settings.json` — Settings must not be required to initialize appearance
