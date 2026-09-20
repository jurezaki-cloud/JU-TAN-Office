"""JU-TAN Office desktop licensing client."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API_BASE = os.getenv("JU_TAN_LICENSE_API", "https://ju-tan.com/api/v1/licenses").rstrip("/")
APP_VERSION = "1.0.0"
STATE_DIR = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "JU-TAN" / "Office"
STATE_FILE = STATE_DIR / "license.json"


class LicenseError(RuntimeError):
    pass


@dataclass
class LicenseState:
    activation_token: str
    device_id: str
    company_name: str = ""
    grace_until: str = ""

    @classmethod
    def load(cls) -> "LicenseState | None":
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return cls(
                activation_token=data["activation_token"],
                device_id=data["device_id"],
                company_name=data.get("company_name", ""),
                grace_until=data.get("grace_until", ""),
            )
        except (OSError, KeyError, ValueError, TypeError):
            return None

    def save(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.__dict__), encoding="utf-8")


def _windows_machine_guid() -> str:
    if platform.system() != "Windows":
        return ""
    try:
        out = subprocess.check_output(
            ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return out.strip().split()[-1]
    except Exception:
        return ""


def device_id() -> str:
    """Return the API-required 64-char SHA-256 device fingerprint."""
    raw = "|".join(
        [
            _windows_machine_guid(),
            platform.node(),
            platform.machine(),
            str(uuid.getnode()),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{API_BASE}/{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "JU-TAN-Office"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            message = body.get("error") or body.get("code") or f"HTTP {exc.code}"
        except Exception:
            message = f"HTTP {exc.code}"
        raise LicenseError(str(message)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LicenseError("Licenčni strežnik trenutno ni dosegljiv.") from exc


def activate(license_key: str) -> LicenseState:
    did = device_id()
    result = _post("activate", {
        "license_key": license_key.strip(),
        "device_id": did,
        "app_version": APP_VERSION,
    })
    token = result.get("activation_token")
    if not token:
        raise LicenseError("Strežnik ni vrnil aktivacijskega žetona.")
    state = LicenseState(
        activation_token=token,
        device_id=did,
        company_name=result.get("company_name", ""),
        grace_until=result.get("grace_until", ""),
    )
    state.save()
    return state


def validate(state: LicenseState) -> dict[str, Any]:
    return _post("validate", {
        "activation_token": state.activation_token,
        "device_id": state.device_id,
        "app_version": APP_VERSION,
    })


def deactivate(state: LicenseState) -> None:
    _post("deactivate", {
        "activation_token": state.activation_token,
        "device_id": state.device_id,
    })
    try:
        STATE_FILE.unlink()
    except FileNotFoundError:
        pass
