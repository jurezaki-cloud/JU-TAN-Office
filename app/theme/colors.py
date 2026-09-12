from enum import Enum


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class LightColors:
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    BACKGROUND = "#F8FAFC"
    SURFACE = "#FFFFFF"
    BORDER = "#E2E8F0"
    TEXT = "#0F172A"
    SECONDARY = "#64748B"
    SUCCESS = "#16A34A"
    SUCCESS_HOVER = "#15803D"
    WARNING = "#F59E0B"
    WARNING_HOVER = "#D97706"
    DANGER = "#DC2626"
    DANGER_HOVER = "#B91C1C"
    TABLE_HEADER = "#F1F5F9"
    TABLE_ALTERNATE = "#F8FAFC"
    SIDEBAR_BG = "#0F172A"
    SIDEBAR_HOVER = "#1E293B"
    SIDEBAR_PRESSED = "#334155"
    SIDEBAR_TEXT = "#F8FAFC"
    SIDEBAR_MUTED = "#94A3B8"
    SIDEBAR_ACTIVE = "rgba(37, 99, 235, 0.22)"
    ON_PRIMARY = "#FFFFFF"


class DarkColors:
    """Pripravljena paleta za prihodnji Dark Theme."""

    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2563EB"
    BACKGROUND = "#0F172A"
    SURFACE = "#1E293B"
    BORDER = "#334155"
    TEXT = "#F8FAFC"
    SECONDARY = "#94A3B8"
    SUCCESS = "#22C55E"
    SUCCESS_HOVER = "#16A34A"
    WARNING = "#FBBF24"
    WARNING_HOVER = "#F59E0B"
    DANGER = "#F87171"
    DANGER_HOVER = "#DC2626"
    TABLE_HEADER = "#1E293B"
    TABLE_ALTERNATE = "#162032"
    SIDEBAR_BG = "#020617"
    SIDEBAR_HOVER = "#1E293B"
    SIDEBAR_PRESSED = "#334155"
    SIDEBAR_TEXT = "#F8FAFC"
    SIDEBAR_MUTED = "#64748B"
    SIDEBAR_ACTIVE = "rgba(59, 130, 246, 0.24)"
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
