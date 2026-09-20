"""Reusable update security policy (no download / no installer execution)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.constants import APP_VERSION
from app.core.update_manifest import (
    ALLOWED_CHANNELS,
    Artifact,
    ManifestError,
    UpdateManifest,
    validate_https_url,
    validate_safe_filename,
    validate_sha256_hex,
)
from app.core.update_signing import VerificationError, verify_manifest_signature
from app.core.update_trust import VerificationKeyStore, production_key_store
from app.core.versioning import VersionError, parse_semver


class UpdatePolicyError(ValueError):
    """Update rejected by security policy."""


def compare_versions(left: str, right: str) -> int:
    """Return -1 / 0 / 1 for left < / == / > right (strict semver)."""
    a = parse_semver(left)
    b = parse_semver(right)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def require_newer_version(candidate: str, current: str = APP_VERSION) -> None:
    try:
        cmp = compare_versions(candidate, current)
    except VersionError as exc:
        raise UpdatePolicyError(str(exc)) from exc
    if cmp == 0:
        raise UpdatePolicyError(f"equal version rejected: {candidate}")
    if cmp < 0:
        raise UpdatePolicyError(f"downgrade rejected: {candidate} < {current}")


def require_min_version_compatible(min_version: str, current: str = APP_VERSION) -> None:
    try:
        if compare_versions(current, min_version) < 0:
            raise UpdatePolicyError(
                f"min_version incompatibility: current {current} < required {min_version}"
            )
    except VersionError as exc:
        raise UpdatePolicyError(str(exc)) from exc


def require_channel(channel: str, *, allowed: frozenset[str] | None = None) -> str:
    normalized = (channel or "").strip().lower()
    accepted = allowed or ALLOWED_CHANNELS
    if normalized not in accepted:
        raise UpdatePolicyError(f"channel validation failed: {channel!r}")
    return normalized


def require_safe_filename(filename: str) -> str:
    try:
        return validate_safe_filename(filename)
    except ManifestError as exc:
        raise UpdatePolicyError(str(exc)) from exc


def require_https_url(url: str, *, field: str = "url") -> str:
    try:
        return validate_https_url(url, field=field, allow_empty=False)
    except ManifestError as exc:
        raise UpdatePolicyError(str(exc)) from exc


def verify_sha256_file(path: Path | str, expected_hex: str) -> str:
    digest_expected = validate_sha256_hex(expected_hex)
    path = Path(path)
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if digest != digest_expected:
        raise UpdatePolicyError(
            f"SHA-256 mismatch for {path.name}: got {digest}, expected {digest_expected}"
        )
    return digest


def verify_artifact_size(path: Path | str, expected_size: int) -> int:
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size <= 0:
        raise UpdatePolicyError(f"invalid expected size: {expected_size!r}")
    path = Path(path)
    actual = path.stat().st_size
    if actual != expected_size:
        raise UpdatePolicyError(
            f"artifact size mismatch for {path.name}: got {actual}, expected {expected_size}"
        )
    return actual


def verify_artifact_file(path: Path | str, artifact: Artifact) -> None:
    path = Path(path)
    require_safe_filename(artifact.filename)
    if path.name != artifact.filename:
        raise UpdatePolicyError(
            f"artifact filename mismatch: file {path.name!r} != manifest {artifact.filename!r}"
        )
    verify_artifact_size(path, artifact.size)
    verify_sha256_file(path, artifact.sha256)


def evaluate_update_eligibility(
    manifest: UpdateManifest,
    *,
    current_version: str = APP_VERSION,
    allowed_channels: frozenset[str] | None = None,
    key_store: VerificationKeyStore | None = None,
    verify_signature: bool = True,
) -> UpdateManifest:
    """Validate a signed manifest for upgrade eligibility without downloading."""
    if verify_signature:
        try:
            manifest = verify_manifest_signature(
                manifest, key_store=key_store or production_key_store()
            )
        except VerificationError as exc:
            raise UpdatePolicyError(str(exc)) from exc

    require_channel(manifest.channel, allowed=allowed_channels)
    require_newer_version(manifest.version, current_version)
    require_min_version_compatible(manifest.min_version, current_version)

    for artifact in manifest.artifacts:
        require_safe_filename(artifact.filename)
        if artifact.url:
            require_https_url(artifact.url, field="artifact.url")
        validate_sha256_hex(artifact.sha256)
        if artifact.size <= 0:
            raise UpdatePolicyError(f"invalid artifact size: {artifact.size}")

    if manifest.notes_url:
        require_https_url(manifest.notes_url, field="notes_url")

    return manifest
