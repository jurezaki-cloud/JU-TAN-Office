"""Nadgradnja: primerjava verzij, signed manifest, backup, rollback."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from app.core.constants import APP_VERSION, BASE_DIR, DATA_DIR, DATABASE_PATH
from app.core.logger import logger
from app.core.permissions import audit, require
from app.modules.settings.settings_controller import SettingsController

VERSION_MARK = DATA_DIR / "app_version.txt"
UPDATE_FEED_ENV = "JU_TAN_UPDATE_URL"
UPDATE_REQUIRE_SIG_ENV = "JU_TAN_UPDATE_REQUIRE_SIGNATURE"
PRODUCTION_VERIFY_KEY = (
    BASE_DIR / "resources" / "update_keys" / "production" / "manifest_hmac.hex"
)


class UpdateError(RuntimeError):
    pass


def parse_version(text: str) -> tuple[int, int, int]:
    parts = []
    for chunk in (text or "0").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits or 0))
        if len(parts) == 3:
            break
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def is_newer(candidate: str, current: str = APP_VERSION) -> bool:
    return parse_version(candidate) > parse_version(current)


def read_latest(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _local_latest_path(source: Path | None = None) -> Path:
    if source is not None:
        return source
    try:
        from app.core.deploy_paths import install_root

        return install_root() / "updates" / "latest.json"
    except Exception:
        return Path(__file__).resolve().parent.parent.parent / "updates" / "latest.json"


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def fetch_remote_manifest(url: str) -> dict:
    """Fetch update manifest over HTTPS only."""
    target = (url or "").strip()
    if not target.lower().startswith("https://"):
        raise UpdateError("Kanal posodobitev mora uporabljati HTTPS.")
    req = urllib.request.Request(
        target,
        headers={"User-Agent": f"JU-TAN-Office/{APP_VERSION}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=_ssl_context()) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise UpdateError("Kanala posodobitev trenutno ni mogoče doseči.") from exc
    if not isinstance(data, dict):
        raise UpdateError("Neveljaven odziv kanala posodobitev.")
    return data


def canonical_manifest(payload: dict) -> bytes:
    """Stable JSON bytes used for HMAC (signature field excluded)."""
    body = {k: v for k, v in payload.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _load_verify_key() -> bytes | None:
    override = os.getenv("JU_TAN_UPDATE_HMAC_KEY", "").strip()
    if override:
        try:
            return bytes.fromhex(override) if all(c in "0123456789abcdefABCDEF" for c in override) else override.encode(
                "utf-8"
            )
        except ValueError:
            return override.encode("utf-8")
    if PRODUCTION_VERIFY_KEY.is_file():
        hex_key = PRODUCTION_VERIFY_KEY.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if hex_key and not hex_key.startswith("#"):
            try:
                return bytes.fromhex(hex_key)
            except ValueError:
                return None
    return None


def verify_manifest_signature(payload: dict) -> bool:
    signature = str(payload.get("signature") or "").strip().lower()
    if not signature:
        return False
    key = _load_verify_key()
    if key is None:
        return False
    expect = hmac.new(key, canonical_manifest(payload), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expect)


def _require_signature() -> bool:
    flag = os.getenv(UPDATE_REQUIRE_SIG_ENV, "").strip().lower()
    return flag in {"1", "true", "yes"}


def validate_manifest(payload: dict) -> dict:
    """
    Commercial readiness checks for update manifests.

    - version required
    - download url must be HTTPS when present
    - sha256 (64 hex) required when url is present
    - signature verified when present; required when JU_TAN_UPDATE_REQUIRE_SIGNATURE=1
    """
    if not isinstance(payload, dict):
        raise UpdateError("Neveljaven manifesto posodobitve.")
    version = str(payload.get("version") or "").strip()
    if not version:
        raise UpdateError("Manifestu manjka različica.")

    url = str(payload.get("url") or "").strip()
    sha = str(payload.get("sha256") or "").strip().lower()
    if url:
        if not url.lower().startswith("https://"):
            raise UpdateError("URL posodobitve mora uporabljati HTTPS.")
        if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
            raise UpdateError("Za prenos posodobitve je zahtevan veljaven SHA-256.")

    signature = str(payload.get("signature") or "").strip()
    if signature:
        if not verify_manifest_signature(payload):
            raise UpdateError("Podpis manifesta posodobitve ni veljaven.")
    elif url and _require_signature():
        raise UpdateError("Zahtevan je podpisan manifesto posodobitve.")

    return payload


def check_for_update(source: Path | None = None) -> dict | None:
    """Preveri lokalni latest.json ali oddaljeni kanal (JU_TAN_UPDATE_URL)."""
    remote = os.getenv(UPDATE_FEED_ENV, "").strip()
    payload: dict | None
    if remote:
        try:
            payload = fetch_remote_manifest(remote)
        except UpdateError:
            # Fall back to bundled local channel when remote is unreachable.
            payload = read_latest(_local_latest_path(source))
            if payload is None:
                raise
    else:
        payload = read_latest(_local_latest_path(source))

    if not payload:
        return None
    validated = validate_manifest(payload)
    remote_ver = str(validated.get("version") or "")
    if remote_ver and is_newer(remote_ver):
        return validated
    return None


def backup_for_upgrade() -> Path:
    require("backup")
    controller = SettingsController()
    target = controller.backup_database()
    audit("upgrade-backup", str(target))
    logger.info("Varnostna kopija pred nadgradnjo: %s", target)
    return target


def rollback(backup: Path) -> None:
    require("backup")
    SettingsController().restore_database(backup)
    audit("upgrade-rollback", str(backup))
    logger.warning("Obnova baze po napaki nadgradnje: %s", backup)


def apply_schema_upgrade() -> None:
    """Po zamenjavi datotek: inicializiraj shemo, ob napaki rollback."""
    from app.database.database import db
    from app.core.setup_state import ensure_schema_version

    previous = VERSION_MARK.read_text(encoding="utf-8").strip() if VERSION_MARK.exists() else ""
    if previous == APP_VERSION:
        # Schema compatibility migrations must still run even when the app
        # version did not change. Branch restores can change the expected DB
        # shape while retaining the same public version number.
        db.initialize()
        ensure_schema_version()
        return
    backup = None
    if previous and DATABASE_PATH.exists():
        backup = backup_for_upgrade()
    try:
        db.initialize()
        ensure_schema_version()
        VERSION_MARK.write_text(APP_VERSION, encoding="utf-8")
        logger.info("Nadgradnja na %s uspešna (prej %s)", APP_VERSION, previous or "nova namestitev")
    except Exception:
        if backup is not None:
            rollback(backup)
        raise
