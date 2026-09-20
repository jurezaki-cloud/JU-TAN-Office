"""Signed update manifest: schema, canonical JSON, strict validation."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from app.core.versioning import VersionError, parse_semver

MANIFEST_SCHEMA = "ju-tan.update.manifest.v1"
ALLOWED_CHANNELS = frozenset({"gold", "stable", "beta", "dev"})
ALLOWED_PRODUCTS = frozenset({"ju-tan-office"})
ALLOWED_ARTIFACT_KINDS = frozenset({"installer", "portable", "delta"})
ALLOWED_SIGNATURE_ALGS = frozenset({"ed25519"})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ManifestError(ValueError):
    """Manifest structural or semantic validation failure."""


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    filename: str
    size: int
    sha256: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "filename": self.filename,
            "size": self.size,
            "sha256": self.sha256,
            "url": self.url,
        }


@dataclass(frozen=True)
class Signature:
    alg: str
    key_id: str
    value: str

    def to_dict(self) -> dict[str, Any]:
        return {"alg": self.alg, "key_id": self.key_id, "value": self.value}


@dataclass(frozen=True)
class UpdateManifest:
    schema: str
    channel: str
    product: str
    version: str
    min_version: str
    published_at: str
    notes_sl: str
    notes_url: str
    artifacts: tuple[Artifact, ...]
    signature: Signature | None

    def to_dict(self, *, include_signature: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "channel": self.channel,
            "product": self.product,
            "version": self.version,
            "min_version": self.min_version,
            "published_at": self.published_at,
            "notes_sl": self.notes_sl,
            "notes_url": self.notes_url,
            "artifacts": [item.to_dict() for item in self.artifacts],
        }
        if include_signature and self.signature is not None:
            payload["signature"] = self.signature.to_dict()
        return payload


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Deterministic UTF-8 JSON used for signing/verification (signature excluded by caller)."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def signing_payload_bytes(manifest: UpdateManifest | Mapping[str, Any]) -> bytes:
    if isinstance(manifest, UpdateManifest):
        body = manifest.to_dict(include_signature=False)
    else:
        body = {k: v for k, v in dict(manifest).items() if k != "signature"}
    return canonical_json_bytes(body)


def _require_str(obj: Mapping[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str):
        raise ManifestError(f"Field {key!r} must be a string")
    return value


def _require_nonempty_str(obj: Mapping[str, Any], key: str) -> str:
    value = _require_str(obj, key).strip()
    if not value:
        raise ManifestError(f"Field {key!r} must be non-empty")
    return value


def validate_safe_filename(filename: str) -> str:
    name = filename or ""
    if not name or name in {".", ".."}:
        raise ManifestError(f"Unsafe filename: {filename!r}")
    if "/" in name or "\\" in name or "\x00" in name:
        raise ManifestError(f"Path traversal / separators in filename: {filename!r}")
    if ".." in name:
        raise ManifestError(f"Path traversal in filename: {filename!r}")
    if not _SAFE_FILENAME_RE.fullmatch(name):
        raise ManifestError(f"Unsafe filename: {filename!r}")
    return name


def validate_sha256_hex(value: str) -> str:
    digest = (value or "").strip().lower()
    if not _SHA256_RE.fullmatch(digest):
        raise ManifestError(f"Invalid SHA-256: {value!r}")
    return digest


def validate_https_url(url: str, *, field: str = "url", allow_empty: bool = False) -> str:
    text = (url or "").strip()
    if not text:
        if allow_empty:
            return ""
        raise ManifestError(f"{field} must be a non-empty HTTPS URL")
    parsed = urlparse(text)
    if parsed.scheme.lower() != "https":
        raise ManifestError(f"Non-HTTPS URL rejected for {field}: {url!r}")
    if not parsed.netloc:
        raise ManifestError(f"Malformed URL for {field}: {url!r}")
    return text


def _parse_artifact(raw: Any, *, require_https: bool) -> Artifact:
    if not isinstance(raw, dict):
        raise ManifestError("Each artifact must be an object")
    art_id = _require_nonempty_str(raw, "id")
    kind = _require_nonempty_str(raw, "kind")
    if kind not in ALLOWED_ARTIFACT_KINDS:
        raise ManifestError(f"Unsupported artifact kind: {kind!r}")
    filename = validate_safe_filename(_require_nonempty_str(raw, "filename"))
    size = raw.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ManifestError(f"Artifact size must be a positive integer, got {size!r}")
    sha256 = validate_sha256_hex(_require_nonempty_str(raw, "sha256"))
    url_raw = _require_str(raw, "url")
    if require_https:
        url = validate_https_url(url_raw, field="artifact.url", allow_empty=False)
    else:
        # Offline/dev stubs may omit a download URL; still reject active HTTP.
        text = url_raw.strip()
        if text:
            url = validate_https_url(text, field="artifact.url", allow_empty=False)
        else:
            url = ""
    return Artifact(
        id=art_id,
        kind=kind,
        filename=filename,
        size=size,
        sha256=sha256,
        url=url,
    )


def _parse_signature(raw: Any) -> Signature:
    if not isinstance(raw, dict):
        raise ManifestError("Malformed signature: must be an object")
    alg = _require_nonempty_str(raw, "alg").lower()
    if alg not in ALLOWED_SIGNATURE_ALGS:
        raise ManifestError(f"Unknown signature algorithm: {alg!r}")
    key_id = _require_nonempty_str(raw, "key_id")
    if not _KEY_ID_RE.fullmatch(key_id):
        raise ManifestError(f"Malformed signature key_id: {key_id!r}")
    value = _require_nonempty_str(raw, "value")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:  # noqa: BLE001 — fail closed
        raise ManifestError("Malformed signature value (base64)") from exc
    if len(decoded) != 64:
        raise ManifestError("Malformed signature value (expected 64-byte Ed25519 signature)")
    return Signature(alg=alg, key_id=key_id, value=value)


def parse_manifest(
    data: Mapping[str, Any] | str | bytes,
    *,
    require_signature: bool = True,
    require_https_artifacts: bool = True,
) -> UpdateManifest:
    """Parse and structurally validate a manifest. Does not verify cryptography."""
    if isinstance(data, (bytes, bytearray)):
        try:
            data = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ManifestError("Malformed manifest JSON") from exc
    elif isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ManifestError("Malformed manifest JSON") from exc

    if not isinstance(data, Mapping):
        raise ManifestError("Manifest must be a JSON object")

    schema = _require_nonempty_str(data, "schema")
    if schema != MANIFEST_SCHEMA:
        raise ManifestError(f"Unsupported schema: {schema!r}")

    channel = _require_nonempty_str(data, "channel").lower()
    if channel not in ALLOWED_CHANNELS:
        raise ManifestError(f"Invalid channel: {channel!r}")

    product = _require_nonempty_str(data, "product").lower()
    if product not in ALLOWED_PRODUCTS:
        raise ManifestError(f"Invalid product: {product!r}")

    version = _require_nonempty_str(data, "version")
    min_version = _require_nonempty_str(data, "min_version")
    try:
        parse_semver(version)
        parse_semver(min_version)
    except VersionError as exc:
        raise ManifestError(str(exc)) from exc

    published_at = _require_nonempty_str(data, "published_at")
    notes_sl = _require_str(data, "notes_sl")
    notes_url = _require_str(data, "notes_url").strip()
    if notes_url:
        validate_https_url(notes_url, field="notes_url", allow_empty=False)

    artifacts_raw = data.get("artifacts")
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise ManifestError("artifacts must be a non-empty array")
    artifacts = tuple(
        _parse_artifact(item, require_https=require_https_artifacts) for item in artifacts_raw
    )

    signature: Signature | None = None
    if "signature" in data and data["signature"] is not None:
        signature = _parse_signature(data["signature"])
    elif require_signature:
        raise ManifestError("Missing signature")

    return UpdateManifest(
        schema=schema,
        channel=channel,
        product=product,
        version=version,
        min_version=min_version,
        published_at=published_at,
        notes_sl=notes_sl,
        notes_url=notes_url,
        artifacts=artifacts,
        signature=signature,
    )


def load_manifest_file(
    path: str | bytes,
    *,
    require_signature: bool = True,
    require_https_artifacts: bool = True,
) -> UpdateManifest:
    from pathlib import Path

    text = Path(path).read_text(encoding="utf-8")
    return parse_manifest(
        text,
        require_signature=require_signature,
        require_https_artifacts=require_https_artifacts,
    )


def dumps_manifest(manifest: UpdateManifest, *, pretty: bool = True) -> str:
    payload = manifest.to_dict(include_signature=True)
    if pretty:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return canonical_json_bytes(payload).decode("utf-8")
