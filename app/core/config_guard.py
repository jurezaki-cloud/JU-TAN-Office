"""Checksum in selitev nastavitev."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.core.constants import APP_VERSION

CONFIG_VERSION = 1


def checksum(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def stamp(data: dict) -> dict:
    payload = dict(data)
    payload.pop("_checksum", None)
    payload["config_version"] = int(payload.get("config_version") or CONFIG_VERSION)
    payload["app_version"] = APP_VERSION
    payload["_checksum"] = checksum({k: v for k, v in payload.items() if k != "_checksum"})
    return payload


def valid(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    stored = data.get("_checksum")
    if not stored:
        return False
    check = {k: v for k, v in data.items() if k != "_checksum"}
    return stored == checksum(check)


def migrate(data: dict, defaults: dict) -> dict:
    merged = _deep(defaults, data if isinstance(data, dict) else {})
    try:
        version = int(merged.get("config_version") or 0)
    except (TypeError, ValueError):
        version = 0
    if version < CONFIG_VERSION:
        merged["config_version"] = CONFIG_VERSION
    if not merged.get("app_version"):
        merged["app_version"] = APP_VERSION
    return merged


def _deep(base: dict, incoming: dict) -> dict:
    out = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep(out[key], value)
        else:
            out[key] = value
    return out


def write_sidecar(path: Path, digest: str) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(digest, encoding="utf-8")
