"""Arrow, check-mark and radio-dot images referenced from theme.qss.

Qt styles paint CSS border triangles differently (Windows 11 fills the whole
rectangle) and native check/radio indicators ignore the stylesheet colours, so
every indicator is an SVG in the palette's colours. The chevrons use TEXT_MUTED
(DISABLED when disabled); the check mark and dot use ON_PRIMARY on a PRIMARY fill.
"""

from __future__ import annotations

from pathlib import Path

from app.theme.colors import ThemeMode

ICON_DIR = Path(__file__).resolve().parent / "icons"


def _url(name: str) -> str:
    # Quoted because the install path may contain spaces; forward slashes because a
    # backslash starts an escape inside a CSS string.
    return '"' + (ICON_DIR / name).as_posix() + '"'


def indicator_tokens(mode: ThemeMode) -> dict[str, str]:
    """``{{TOKEN}}`` values for theme.qss in *mode*."""
    theme = "dark" if mode == ThemeMode.DARK else "light"
    return {
        "ARROW_DOWN": _url(f"chevron-down-{theme}.svg"),
        "ARROW_DOWN_DISABLED": _url(f"chevron-down-disabled-{theme}.svg"),
        "ARROW_UP": _url(f"chevron-up-{theme}.svg"),
        "ARROW_UP_DISABLED": _url(f"chevron-up-disabled-{theme}.svg"),
        "CHECK_MARK": _url("check.svg"),
        "RADIO_DOT": _url("radio-dot.svg"),
    }
