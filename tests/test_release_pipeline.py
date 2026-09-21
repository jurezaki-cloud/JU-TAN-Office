"""Release pipeline structural tests — scripts, signing surface, version sync."""

from __future__ import annotations

import re
from pathlib import Path

from app.core.constants import APP_CHANNEL, APP_VERSION, SCHEMA_VERSION
from app.core import release_meta as meta


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_build_release_script_exists():
    path = ROOT / "scripts" / "build_release.ps1"
    assert path.is_file()
    text = _read("scripts/build_release.ps1")
    assert "JU-TAN OFFICE RELEASE PIPELINE" in text
    assert "RELEASE READY" in text
    assert "Set-StrictMode -Version Latest" in text
    assert '$ErrorActionPreference = "Stop"' in text
    assert "MyInvocation.MyCommand.Path" in text
    assert "Sign-Installer" in text
    assert "Create-Checksum" in text
    assert "Verify-Signature" in text
    assert "Find-SignTool" in text
    assert "Find-CodeSigningCertificate" in text
    assert "dist/SHA256SUMS.txt" in text or "SHA256SUMS.txt" in text
    assert "AuthenticodeSigning.ps1" in text


def test_signing_helper_functions_exist():
    lib = _read("scripts/AuthenticodeSigning.ps1")
    for name in (
        "function Find-SignTool",
        "function Find-CodeSigningCertificate",
        "function Verify-Signature",
        "function Invoke-AuthenticodeSign",
        "function Test-JuTanSigningReady",
    ):
        assert name in lib, f"missing {name}"
    assert "Cert:\\CurrentUser\\My" in lib
    assert "CN=JU-TAN Studio" in lib
    assert "/sha1" in lib
    assert "/pa" in lib
    assert "JU_TAN_PFX" in lib  # backward-compatible fallback


def test_checksum_generation_exists():
    build = _read("scripts/build_release.ps1")
    assert "function Create-Checksum" in build
    assert "SHA256" in build
    assert "SHA256SUMS.txt" in build
    # Checksums must run after installer signing
    sign_at = build.index("Sign-Installer")
    checksum_at = build.index("Create-Checksum -DistDir")
    assert sign_at < checksum_at


def test_version_consistency_across_packaging():
    assert meta.APP_VERSION == APP_VERSION
    assert meta.APP_CHANNEL == APP_CHANNEL
    assert meta.SCHEMA_VERSION == SCHEMA_VERSION

    version_txt = _read("packaging/Version.txt")
    assert f"Version: {APP_VERSION} {APP_CHANNEL}" in version_txt
    assert f"SCHEMA {SCHEMA_VERSION}" in version_txt

    version_iss = _read("packaging/version.iss")
    assert f'MyAppVersion "{APP_VERSION}"' in version_iss
    assert f'MySchemaVersion "{SCHEMA_VERSION}"' in version_iss

    root_version = _read("Version.txt")
    assert f"Version: {APP_VERSION} {APP_CHANNEL}" in root_version


def test_signing_documentation_covers_store_and_verify():
    text = _read("docs/SIGNING.md")
    assert "CN=JU-TAN Studio" in text
    assert "Cert:\\CurrentUser\\My" in text or "Cert:\\CurrentUser\\My" in text
    assert "Find-CodeSigningCertificate" in text
    assert "signtool verify" in text
    assert "/pa" in text
    assert "SHA256SUMS" in text
    assert "production certificate migration" in text.lower() or "Production certificate migration" in text
    assert "JU_TAN_PFX" in text
    assert "RequireSigned" in text or "JU_TAN_REQUIRE_SIGNED" in text


def test_no_stale_schema_version_one_in_guides():
    for rel in ("docs/ADMIN_GUIDE.md", "docs/USER_GUIDE.md", "docs/RELEASE_REPORT.md"):
        text = _read(rel)
        assert "SCHEMA_VERSION = 1" not in text
        assert not re.search(r"SCHEMA_VERSION\s*=\s*1\b", text)


def test_admin_guide_matches_current_schema():
    text = _read("docs/ADMIN_GUIDE.md")
    assert f"SCHEMA_VERSION = {SCHEMA_VERSION}" in text
