"""Public verification key store for update manifests.

CLIENT TRUST MATERIAL ONLY — never place private signing keys here.
Production keys live under ``resources/update_keys/production/``.
Test keys must not be packaged into the application.
"""

from __future__ import annotations

import base64
from pathlib import Path

from nacl.signing import VerifyKey

from app.core.constants import BASE_DIR, RESOURCE_DIR

PRODUCTION_KEYS_DIR = RESOURCE_DIR / "update_keys" / "production"
TEST_KEYS_DIR = BASE_DIR / "tests" / "fixtures" / "update_keys"


class TrustError(RuntimeError):
    """Trusted key loading failure."""


class VerificationKeyStore:
    """Fail-closed map of ``key_id`` → ``VerifyKey``."""

    def __init__(self, keys: dict[str, VerifyKey] | None = None) -> None:
        self._keys: dict[str, VerifyKey] = dict(keys or {})

    def __contains__(self, key_id: object) -> bool:
        return isinstance(key_id, str) and key_id in self._keys

    def get(self, key_id: str) -> VerifyKey:
        try:
            return self._keys[key_id]
        except KeyError as exc:
            raise KeyError(key_id) from exc

    def key_ids(self) -> frozenset[str]:
        return frozenset(self._keys)

    def register(self, key_id: str, verify_key: VerifyKey) -> None:
        if not key_id or not isinstance(key_id, str):
            raise TrustError("Invalid key_id")
        self._keys[key_id] = verify_key

    def merge(self, other: "VerificationKeyStore") -> "VerificationKeyStore":
        merged = VerificationKeyStore(self._keys)
        for key_id in other.key_ids():
            merged.register(key_id, other.get(key_id))
        return merged


def decode_public_key_bytes(raw: bytes) -> bytes:
    data = raw.strip()
    if len(data) == 32:
        return data
    text = data.decode("ascii", errors="strict").strip()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-----"):
            continue
        text = line
        break
    try:
        key = base64.b64decode(text, validate=True)
    except Exception:
        try:
            key = bytes.fromhex(text)
        except Exception as exc:  # noqa: BLE001
            raise TrustError("Unrecognized public key encoding") from exc
    if len(key) != 32:
        raise TrustError(f"Ed25519 public key must be 32 bytes, got {len(key)}")
    return key


def load_verify_key(raw: bytes) -> VerifyKey:
    return VerifyKey(decode_public_key_bytes(raw))


def load_key_store_from_dir(directory: Path) -> VerificationKeyStore:
    store = VerificationKeyStore()
    if not directory.is_dir():
        return store
    for path in sorted(directory.glob("*.pub")):
        key_id = path.stem
        store.register(key_id, load_verify_key(path.read_bytes()))
    return store


_production_store: VerificationKeyStore | None = None


def production_key_store(*, reload: bool = False) -> VerificationKeyStore:
    """Return the packaged production public-key store (may be empty until keys are issued)."""
    global _production_store
    if _production_store is None or reload:
        _production_store = load_key_store_from_dir(PRODUCTION_KEYS_DIR)
    return _production_store


def test_key_store() -> VerificationKeyStore:
    """Load deterministic test keys (tests only — never for production trust)."""
    return load_key_store_from_dir(TEST_KEYS_DIR)


def packaged_private_key_paths(root: Path | None = None) -> list[Path]:
    """Locate accidental private key material under packaged/runtime trees."""
    base = root or BASE_DIR
    suspects: list[Path] = []
    patterns = (
        "**/update_keys/**/*.key",
        "**/update_keys/**/*.pem",
        "**/update_keys/private/**",
        "**/update_keys/**/*secret*",
        "**/update_keys/**/*private*",
    )
    search_roots = [
        base / "resources",
        base / "app",
        base / "updates",
        base / "packaging",
        base / "dist",
    ]
    for root_dir in search_roots:
        if not root_dir.exists():
            continue
        for pattern in patterns:
            for path in root_dir.glob(pattern):
                if path.is_file():
                    suspects.append(path)
    return suspects
