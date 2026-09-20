"""Ed25519 update-manifest signing and verification (fail-closed)."""

from __future__ import annotations

import base64
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from app.core.update_manifest import (
    ManifestError,
    Signature,
    UpdateManifest,
    parse_manifest,
    signing_payload_bytes,
)
from app.core.update_trust import VerificationKeyStore, production_key_store


class SigningError(RuntimeError):
    """Signing credential or operation failure."""


class VerificationError(RuntimeError):
    """Signature verification failure (fail closed)."""


def load_signing_key_bytes(raw: bytes) -> SigningKey:
    data = raw.strip()
    if not data:
        raise SigningError("Empty signing key material")
    # Accept raw 32-byte seed, hex, or base64.
    if len(data) == 32:
        seed = data
    else:
        text = data.decode("ascii", errors="strict").strip()
        if text.startswith("-----"):
            raise SigningError(
                "PEM private keys are not supported; supply raw/base64/hex Ed25519 seed"
            )
        seed = None
        for decoder in (
            lambda t: bytes.fromhex(t),
            lambda t: base64.b64decode(t, validate=True),
        ):
            try:
                candidate = decoder(text)
            except Exception:
                continue
            if len(candidate) == 32:
                seed = candidate
                break
            if len(candidate) == 64:
                # libsodium secret key = seed || public; use seed half
                seed = candidate[:32]
                break
        if seed is None:
            raise SigningError("Unrecognized Ed25519 private key encoding")
    try:
        return SigningKey(seed)
    except Exception as exc:  # noqa: BLE001
        raise SigningError("Invalid Ed25519 private key") from exc


def load_signing_key_from_file(path: Path | str) -> SigningKey:
    path = Path(path)
    if not path.is_file():
        raise SigningError(f"Signing key file not found: {path}")
    return load_signing_key_bytes(path.read_bytes())


def load_signing_key_from_env(
    *,
    env_var: str = "JU_TAN_UPDATE_SIGNING_KEY",
    file_env_var: str = "JU_TAN_UPDATE_SIGNING_KEY_FILE",
    environ: dict[str, str] | None = None,
) -> SigningKey:
    import os

    env = environ if environ is not None else os.environ
    file_path = (env.get(file_env_var) or "").strip()
    if file_path:
        return load_signing_key_from_file(file_path)
    inline = (env.get(env_var) or "").strip()
    if inline:
        return load_signing_key_bytes(inline.encode("ascii"))
    raise SigningError(
        "Production signing credentials missing: set "
        f"{file_env_var} (preferred) or {env_var}"
    )


def public_key_b64(verify_key: VerifyKey) -> str:
    return base64.b64encode(bytes(verify_key)).decode("ascii")


def sign_manifest(
    manifest: UpdateManifest,
    signing_key: SigningKey,
    *,
    key_id: str,
) -> UpdateManifest:
    """Return a copy of ``manifest`` with an Ed25519 signature attached."""
    payload = signing_payload_bytes(manifest)
    signed = signing_key.sign(payload)
    signature = Signature(
        alg="ed25519",
        key_id=key_id,
        value=base64.b64encode(signed.signature).decode("ascii"),
    )
    return UpdateManifest(
        schema=manifest.schema,
        channel=manifest.channel,
        product=manifest.product,
        version=manifest.version,
        min_version=manifest.min_version,
        published_at=manifest.published_at,
        notes_sl=manifest.notes_sl,
        notes_url=manifest.notes_url,
        artifacts=manifest.artifacts,
        signature=signature,
    )


def verify_manifest_signature(
    manifest: UpdateManifest | dict,
    *,
    key_store: VerificationKeyStore | None = None,
) -> UpdateManifest:
    """Verify Ed25519 signature using the trusted public-key store (fail closed)."""
    store = key_store or production_key_store()
    if isinstance(manifest, dict):
        parsed = parse_manifest(manifest, require_signature=True, require_https_artifacts=True)
    else:
        parsed = manifest

    if parsed.signature is None:
        raise VerificationError("Missing signature")
    if parsed.signature.alg != "ed25519":
        raise VerificationError(f"Unknown signature algorithm: {parsed.signature.alg!r}")

    try:
        verify_key = store.get(parsed.signature.key_id)
    except KeyError as exc:
        raise VerificationError(f"Unknown key_id: {parsed.signature.key_id!r}") from exc

    try:
        sig_bytes = base64.b64decode(parsed.signature.value, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise VerificationError("Malformed signature value") from exc

    payload = signing_payload_bytes(parsed)
    try:
        verify_key.verify(payload, sig_bytes)
    except BadSignatureError as exc:
        raise VerificationError("Invalid Ed25519 signature") from exc
    except Exception as exc:  # noqa: BLE001
        raise VerificationError("Signature verification failed") from exc

    return parsed


def verify_manifest_json(
    data: str | bytes | dict,
    *,
    key_store: VerificationKeyStore | None = None,
    require_https_artifacts: bool = True,
) -> UpdateManifest:
    parsed = parse_manifest(
        data,
        require_signature=True,
        require_https_artifacts=require_https_artifacts,
    )
    return verify_manifest_signature(parsed, key_store=key_store)
