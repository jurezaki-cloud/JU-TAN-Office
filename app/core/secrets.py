"""Šifriranje občutljivih nastavitev (SMTP, API, licenca, connection string)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

from app.core.constants import DATA_DIR

_PREFIX = b"JT1"
KEY_FILE = DATA_DIR / ".machine_key"


def _machine_key() -> bytes:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = os.urandom(32)
    KEY_FILE.write_bytes(key)
    try:
        KEY_FILE.chmod(0o600)
    except OSError:
        pass
    return key


def _xor(data: bytes, key: bytes) -> bytes:
    stream = hashlib.sha256(key).digest()
    out = bytearray()
    while len(out) < len(data):
        stream = hashlib.sha256(stream + key).digest()
        out.extend(stream)
    return bytes(a ^ b for a, b in zip(data, out[: len(data)]))


def _dpapi_protect(data: bytes) -> bytes | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        crypt32 = ctypes.windll.crypt32
        blob_in = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
        blob_out = DATA_BLOB()
        if not crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            return None
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    except Exception:
        return None


def _dpapi_unprotect(data: bytes) -> bytes | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

        crypt32 = ctypes.windll.crypt32
        blob_in = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
        blob_out = DATA_BLOB()
        if not crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            return None
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    except Exception:
        return None


def encrypt_bytes(plain: bytes) -> str:
    if os.environ.get("JU_TAN_DPAPI") == "1":
        protected = _dpapi_protect(plain)
        if protected is not None:
            return "dpapi:" + base64.b64encode(protected).decode("ascii")
    key = _machine_key()
    nonce = os.urandom(16)
    body = _xor(plain, key + nonce)
    digest = hmac.new(key, nonce + body, hashlib.sha256).digest()
    return "loc1:" + base64.b64encode(_PREFIX + nonce + digest + body).decode("ascii")


def decrypt_bytes(token: str) -> bytes:
    if not token:
        return b""
    if token.startswith("dpapi:"):
        raw = _dpapi_unprotect(base64.b64decode(token.split(":", 1)[1]))
        if raw is None:
            raise ValueError("Skrivnosti ni mogoče odkleniti.")
        return raw
    if token.startswith("loc1:"):
        raw = base64.b64decode(token.split(":", 1)[1])
        if not raw.startswith(_PREFIX):
            raise ValueError("Neveljaven žeton.")
        nonce = raw[3:19]
        digest = raw[19:51]
        body = raw[51:]
        key = _machine_key()
        expect = hmac.new(key, nonce + body, hashlib.sha256).digest()
        if not hmac.compare_digest(digest, expect):
            raise ValueError("Skrivnost je spremenjena.")
        return _xor(body, key + nonce)
    raise ValueError("Neznan format skrivnosti.")


def seal(mapping: dict) -> str:
    payload = json.dumps(mapping or {}, ensure_ascii=False).encode("utf-8")
    return encrypt_bytes(payload)


def reveal(token: str) -> dict:
    if not token:
        return {}
    data = json.loads(decrypt_bytes(token).decode("utf-8"))
    return data if isinstance(data, dict) else {}


SECRET_KEYS = ("smtp_password", "api_key", "license_key", "connection_string")
