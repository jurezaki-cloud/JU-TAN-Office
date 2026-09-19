# JU-TAN Design System

Tokenized QSS theme for JU-TAN Office Enterprise (`app/theme/`).

## Tokens

Defined in `app/theme/colors.py` and injected into `theme.qss` via `ThemeManager`:

| Token | Role |
| --- | --- |
| `PRIMARY` | Brand actions, totals, active nav |
| `ON_PRIMARY` | Text on primary surfaces |
| `BACKGROUND` | App canvas |
| `SURFACE` | Cards, toolbars, dialogs |
| `BORDER` | Hairline separators |
| `TEXT` | Primary copy |
| `SECONDARY` | Muted captions |
| `SUCCESS` / `WARNING` / `DANGER` | Status semantics |
| `CARD_RADIUS` / `CONTROL_RADIUS` | Consistent rounding |

## Rules

- No local ad-hoc stylesheets on pages — use object names + global QSS.
- Status meaning must not rely on color alone (badge text required).
- Totals use `#TotalValue` (emphasised primary).
- Density: tables 48px row height, controls min 36px.
- Charts and KPIs show **real** data only; empty states replace mock samples.

## Shell

- Sidebar: `ModernSidebar` with role-gated modules
- Toolbar: module title + search + user
- Content: stacked lazy pages with consistent 16px spacing
