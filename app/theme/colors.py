from enum import Enum


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class LightColors:
    """Premium light palette — restrained JU-TAN green accent."""

    PRIMARY = "#059669"
    PRIMARY_HOVER = "#047857"
    BACKGROUND = "#F4F6F8"
    SURFACE = "#FFFFFF"
    SURFACE_ELEVATED = "#FFFFFF"
    BORDER = "#E2E8F0"
    TEXT = "#0F172A"
    TEXT_MUTED = "#64748B"
    SECONDARY = "#64748B"
    SUCCESS = "#16A34A"
    SUCCESS_HOVER = "#15803D"
    WARNING = "#D97706"
    WARNING_HOVER = "#B45309"
    # Soft amber for rails / subtle indicators — keep WARNING for semantic text.
    WARNING_SOFT = "rgba(217, 119, 6, 0.45)"
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    INFO = "#2563EB"
    TABLE_HEADER = "#F1F5F9"
    TABLE_ALTERNATE = "#F8FAFC"
    HOVER = "rgba(5, 150, 105, 0.08)"
    SELECTED = "rgba(5, 150, 105, 0.14)"
    FOCUS = "#059669"
    DISABLED = "#94A3B8"
    SIDEBAR_BG = "#0B1220"
    SIDEBAR_HOVER = "#151C2A"
    SIDEBAR_PRESSED = "#1C2636"
    SIDEBAR_TEXT = "#F8FAFC"
    SIDEBAR_MUTED = "#94A3B8"
    SIDEBAR_ACTIVE = "rgba(5, 150, 105, 0.10)"
    SIDEBAR_ACTIVE_EDGE = "#059669"
    ON_PRIMARY = "#FFFFFF"


class DarkColors:
    """Premium dark palette — charcoal/navy layers, restrained accent."""

    PRIMARY = "#10B981"
    PRIMARY_HOVER = "#059669"
    BACKGROUND = "#0B1220"
    SURFACE = "#151D2B"
    SURFACE_ELEVATED = "#1C2636"
    BORDER = "#2A3548"
    TEXT = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    SECONDARY = "#94A3B8"
    SUCCESS = "#22C55E"
    SUCCESS_HOVER = "#16A34A"
    WARNING = "#FBBF24"
    WARNING_HOVER = "#F59E0B"
    # Soft amber for rails / subtle indicators — keep WARNING for semantic text.
    WARNING_SOFT = "rgba(251, 191, 36, 0.40)"
    DANGER = "#F87171"
    DANGER_HOVER = "#EF4444"
    INFO = "#60A5FA"
    TABLE_HEADER = "#1A2332"
    TABLE_ALTERNATE = "#121A27"
    HOVER = "rgba(16, 185, 129, 0.12)"
    SELECTED = "rgba(16, 185, 129, 0.20)"
    FOCUS = "#10B981"
    DISABLED = "#64748B"
    SIDEBAR_BG = "#070B14"
    SIDEBAR_HOVER = "#121A27"
    SIDEBAR_PRESSED = "#1A2332"
    SIDEBAR_TEXT = "#F8FAFC"
    SIDEBAR_MUTED = "#64748B"
    SIDEBAR_ACTIVE = "rgba(16, 185, 129, 0.12)"
    SIDEBAR_ACTIVE_EDGE = "#10B981"
    ON_PRIMARY = "#FFFFFF"


def _palette_from(source) -> dict[str, str]:
    return {
        name: value
        for name, value in vars(source).items()
        if name.isupper() and isinstance(value, str)
    }


PALETTES: dict[ThemeMode, dict[str, str]] = {
    ThemeMode.LIGHT: _palette_from(LightColors),
    ThemeMode.DARK: _palette_from(DarkColors),
}


def current_palette() -> dict[str, str]:
    """Active palette from ThemeManager, falling back to light."""
    try:
        from app.theme.theme import theme_manager

        return dict(PALETTES.get(theme_manager.mode, PALETTES[ThemeMode.LIGHT]))
    except Exception:
        return dict(PALETTES[ThemeMode.LIGHT])


def semantic_color(name: str, fallback: str | None = None) -> str:
    palette = current_palette()
    if name in palette:
        return palette[name]
    if fallback:
        return fallback
    return palette.get("SECONDARY", "#64748B")
