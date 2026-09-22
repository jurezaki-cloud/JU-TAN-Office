"""Shared boolean normalization for settings / PDF options."""

from __future__ import annotations


_FALSE = frozenset({
    "0", "FALSE", "F", "NO", "N", "NE", "OFF", "DISABLED", "DISABLE",
})
_TRUE = frozenset({
    "1", "TRUE", "T", "YES", "Y", "DA", "ON", "ENABLED", "ENABLE",
})


def parse_bool(value, default: bool = True) -> bool:
    """
    Robust boolean parser for persisted settings.

    Accepts bool/int/float and common string forms (true/false, DA/NE, 1/0).
    Never uses ``bool("false")`` — that would incorrectly evaluate to True.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().upper()
    if not text:
        return default
    if text in _FALSE:
        return False
    if text in _TRUE:
        return True
    return default
