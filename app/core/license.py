"""Licenčni sistem: Trial / Professional / Enterprise, offline aktivacija."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date, timedelta
from pathlib import Path

from app.core.constants import APP_VERSION, DATA_DIR

EDITIONS = ("trial", "professional", "enterprise")
LICENSE_PATH = DATA_DIR / "license.json"
_PEPPER = b"JU-TAN-Office-license-v1"


def _sign(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(_PEPPER, blob, hashlib.sha256).hexdigest()


def issue(*, edition: str = "enterprise", days: int = 365, machine: str = "local") -> dict:
    if edition not in EDITIONS:
        raise ValueError("Neznana izdaja licence.")
    payload = {
        "edition": edition,
        "version": APP_VERSION,
        "machine": machine,
        "expires": (date.today() + timedelta(days=days)).isoformat(),
        "offline": True,
    }
    payload["signature"] = _sign({k: v for k, v in payload.items() if k != "signature"})
    return payload


def verify(payload: dict | None) -> bool:
    if not payload or not isinstance(payload, dict):
        return False
    if payload.get("edition") not in EDITIONS:
        return False
    sig = str(payload.get("signature") or "")
    check = {k: v for k, v in payload.items() if k != "signature"}
    if not hmac.compare_digest(sig, _sign(check)):
        return False
    expires = str(payload.get("expires") or "")
    try:
        return date.fromisoformat(expires) >= date.today()
    except ValueError:
        return False


def save(payload: dict, path: Path | None = None) -> Path:
    target = path or LICENSE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def load(path: Path | None = None) -> dict | None:
    target = path or LICENSE_PATH
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def current_edition() -> str:
    payload = load()
    if verify(payload):
        return str(payload.get("edition") or "trial")
    return "trial"


def activate_offline(payload: dict) -> str:
    if not verify(payload):
        raise ValueError("Licenca ni veljavna.")
    save(payload)
    return str(payload["edition"])
