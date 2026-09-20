"""Predpomnilnik uvoženih modulov ob ozadnem ogrevanju."""

from __future__ import annotations

from typing import Any

_MODULES: dict[str, Any] = {}


def remember(name: str, value: Any) -> Any:
    _MODULES[name] = value
    return value


def get(name: str) -> Any:
    return _MODULES.get(name)


def warmup() -> list[str]:
    loaded: list[str] = []
    for name in ("openpyxl", "reportlab", "reportlab.platypus"):
        try:
            __import__(name)
            remember(name, True)
            loaded.append(name)
        except Exception:
            continue
    return loaded
