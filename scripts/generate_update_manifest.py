#!/usr/bin/env python3
"""Generate a signed updates/latest.json manifest for a built Setup.exe.

Fail-closed: production signing credentials must be supplied via
JU_TAN_UPDATE_SIGNING_KEY_FILE (preferred) or JU_TAN_UPDATE_SIGNING_KEY.

Never embeds or generates a production private key.
Does not download or execute installers.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.constants import APP_VERSION  # noqa: E402
from app.core.update_manifest import (  # noqa: E402
    MANIFEST_SCHEMA,
    Artifact,
    UpdateManifest,
    dumps_manifest,
    parse_manifest,
)
from app.core.update_signing import (  # noqa: E402
    SigningError,
    load_signing_key_from_env,
    load_signing_key_from_file,
    public_key_b64,
    sign_manifest,
    verify_manifest_signature,
)
from app.core.update_trust import VerificationKeyStore  # noqa: E402
from app.core.versioning import VersionError, assert_version_sources_consistent  # noqa: E402
from nacl.signing import SigningKey  # noqa: E402


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def build_unsigned_manifest(
    *,
    setup_path: Path,
    version: str,
    channel: str,
    product: str,
    min_version: str,
    notes_sl: str,
    notes_url: str,
    artifact_url: str,
    artifact_id: str,
    published_at: str | None,
) -> UpdateManifest:
    size = setup_path.stat().st_size
    if size <= 0:
        raise SystemExit(f"Setup file is empty: {setup_path}")
    digest = _sha256_file(setup_path)
    artifact = Artifact(
        id=artifact_id,
        kind="installer",
        filename=setup_path.name,
        size=size,
        sha256=digest,
        url=artifact_url,
    )
    return UpdateManifest(
        schema=MANIFEST_SCHEMA,
        channel=channel,
        product=product,
        version=version,
        min_version=min_version,
        published_at=published_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        notes_sl=notes_sl,
        notes_url=notes_url,
        artifacts=(artifact,),
        signature=None,
    )


def resolve_signing_key(args: argparse.Namespace) -> tuple[SigningKey, str]:
    if args.signing_key:
        key = load_signing_key_from_file(args.signing_key)
    else:
        key = load_signing_key_from_env()
    key_id = (args.key_id or "").strip()
    if not key_id:
        raise SigningError("--key-id is required")
    return key, key_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--setup",
        required=True,
        type=Path,
        help="Path to built JU-TAN-Office-Setup.exe",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "updates" / "latest.json",
        help="Output manifest path (default: updates/latest.json)",
    )
    parser.add_argument("--channel", default="gold")
    parser.add_argument("--product", default="ju-tan-office")
    parser.add_argument(
        "--version",
        default="",
        help="Manifest version (default: APP_VERSION)",
    )
    parser.add_argument(
        "--min-version",
        default="1.0.0",
        help="Minimum running version that may apply this update",
    )
    parser.add_argument("--notes-sl", default="")
    parser.add_argument("--notes-url", default="")
    parser.add_argument(
        "--artifact-url",
        required=True,
        help="HTTPS URL for the installer artifact (authenticated portal/CDN)",
    )
    parser.add_argument("--artifact-id", default="setup")
    parser.add_argument("--key-id", required=True, help="Public key id embedded in signature")
    parser.add_argument(
        "--signing-key",
        type=Path,
        default=None,
        help="Path to Ed25519 private seed (else env JU_TAN_UPDATE_SIGNING_KEY_FILE / KEY)",
    )
    parser.add_argument(
        "--skip-version-check",
        action="store_true",
        help="Skip packaging version-drift validation (not for production)",
    )
    args = parser.parse_args(argv)

    setup_path = args.setup.resolve()
    if not setup_path.is_file():
        print(f"ERROR: setup file not found: {setup_path}", file=sys.stderr)
        return 1

    version = (args.version or APP_VERSION).strip()
    if not args.skip_version_check:
        try:
            assert_version_sources_consistent(ROOT)
        except VersionError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if version != APP_VERSION:
            print(
                f"ERROR: --version {version!r} disagrees with APP_VERSION {APP_VERSION!r}",
                file=sys.stderr,
            )
            return 1

    try:
        signing_key, key_id = resolve_signing_key(args)
    except SigningError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    unsigned = build_unsigned_manifest(
        setup_path=setup_path,
        version=version,
        channel=args.channel.lower(),
        product=args.product.lower(),
        min_version=args.min_version,
        notes_sl=args.notes_sl,
        notes_url=args.notes_url,
        artifact_url=args.artifact_url,
        artifact_id=args.artifact_id,
        published_at=None,
    )

    # Structural validation before signing (HTTPS required for release artifacts).
    parse_manifest(
        unsigned.to_dict(include_signature=False),
        require_signature=False,
        require_https_artifacts=True,
    )

    signed = sign_manifest(unsigned, signing_key, key_id=key_id)

    # Verify using the matching public key derived from the signing key only for
    # this generator self-check — not added to the production client trust store.
    self_store = VerificationKeyStore()
    self_store.register(key_id, signing_key.verify_key)
    try:
        verify_manifest_signature(signed, key_store=self_store)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: self-verification failed: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dumps_manifest(signed, pretty=True), encoding="utf-8")
    print(f"Wrote signed manifest: {args.output}")
    print(f"version={version} size={unsigned.artifacts[0].size} sha256={unsigned.artifacts[0].sha256}")
    print(f"key_id={key_id} verify_key_b64={public_key_b64(signing_key.verify_key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
