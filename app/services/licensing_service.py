"""JU-TAN Office desktop licensing client."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import base64
import ctypes
from ctypes import wintypes
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


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi_protect(value: str) -> str:
    if platform.system() != "Windows":
        return value
    raw = value.encode("utf-8")
    buf = ctypes.create_string_buffer(raw)
    in_blob = _DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))
    out_blob = _DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("Windows DPAPI encryption failed")
    try:
        data = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        return "dpapi:" + base64.b64encode(data).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(value: str) -> str:
    if not value.startswith("dpapi:"):
        return value
    raw = base64.b64decode(value[6:])
    buf = ctypes.create_string_buffer(raw)
    in_blob = _DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))
    out_blob = _DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise OSError("Windows DPAPI decryption failed")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


class LicenseError(RuntimeError):
    pass


@dataclass
class LicenseState:
    activation_token: str
    device_id: str
    company_name: str = ""
    grace_until: str = ""
    license_id: str = ""
    device_name: str = ""
    last_seen_at: str = ""
    status: str = ""

    @classmethod
    def load(cls) -> "LicenseState | None":
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return cls(
                activation_token=_dpapi_unprotect(data["activation_token"]),
                device_id=data["device_id"],
                company_name=data.get("company_name", ""),
                grace_until=data.get("grace_until", ""),
                license_id=str(data.get("license_id") or ""),
                device_name=str(data.get("device_name") or ""),
                last_seen_at=str(data.get("last_seen_at") or ""),
                status=str(data.get("status") or ""),
            )
        except (OSError, KeyError, ValueError, TypeError):
            return None

    def save(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = dict(self.__dict__)
        data["activation_token"] = _dpapi_protect(self.activation_token)
        STATE_FILE.write_text(json.dumps(data), encoding="utf-8")

    def apply_server_result(self, result: dict[str, Any]) -> None:
        """Merge validate/activate payload into local license.json fields."""
        from datetime import datetime, timezone

        if result.get("activation_token"):
            self.activation_token = str(result["activation_token"])
        if "company_name" in result and result.get("company_name") is not None:
            self.company_name = str(result.get("company_name") or "")
        if "grace_until" in result and result.get("grace_until") is not None:
            self.grace_until = str(result.get("grace_until") or "")
        if result.get("license_id"):
            self.license_id = str(result["license_id"])
        if result.get("device_name"):
            self.device_name = str(result["device_name"])
        if result.get("status"):
            self.status = str(result["status"])
        self.last_seen_at = str(
            result.get("last_seen_at")
            or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
        if not self.device_name:
            self.device_name = platform.node() or ""


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
        device_name=platform.node() or "",
    )
    state.apply_server_result(result)
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
