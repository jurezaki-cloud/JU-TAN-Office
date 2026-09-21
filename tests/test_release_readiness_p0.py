"""Release readiness P0 — privacy package, version sync, installer polish, splash."""

from __future__ import annotations

from pathlib import Path

from app.core.constants import APP_CHANNEL, APP_VERSION, SCHEMA_VERSION
from app.core.docs_paths import privacy_policy_path
from app.core.release_meta import APP_PUBLISHER_URL, APP_SUPPORT_EMAIL
from app.core.ui.splash_branding import build_splash_pixmap


ROOT = Path(__file__).resolve().parent.parent


def test_privacy_policy_document_exists():
    path = ROOT / "docs" / "PRIVACY.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "GDPR" in text or "zasebnosti" in text.lower()
    assert "JU-TAN" in text
    assert "support@ju-tan.com" in text


def test_privacy_policy_path_resolves_local_doc():
    path = privacy_policy_path()
    assert path is not None
    assert path.name == "PRIVACY.md"
    assert path.is_file()


def test_privacy_card_opens_local_policy(qt_app, monkeypatch):
    from app.widgets.settings import privacy_card as mod

    opened: list[str] = []

    monkeypatch.setattr(
        mod.QDesktopServices,
        "openUrl",
        lambda url: opened.append(url.toLocalFile() or url.toString()),
    )
    monkeypatch.setattr(mod, "toast", lambda *a, **k: None)

    card = mod.PrivacyCard()
    card._open_policy()
    assert opened
    assert opened[0].replace("\\", "/").endswith("docs/PRIVACY.md")
    card.close()


def test_version_txt_matches_constants():
    for rel in ("Version.txt", "packaging/Version.txt"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert f"Version: {APP_VERSION} {APP_CHANNEL}" in text
        assert f"SCHEMA {SCHEMA_VERSION}" in text
        assert APP_PUBLISHER_URL in text
        assert APP_SUPPORT_EMAIL in text


def test_admin_guide_schema_aligned():
    text = (ROOT / "docs" / "ADMIN_GUIDE.md").read_text(encoding="utf-8")
    assert f"SCHEMA_VERSION = {SCHEMA_VERSION}" in text
    assert "SCHEMA_VERSION = 1" not in text


def test_installer_has_publisher_urls_and_docs():
    iss = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
    assert '#include "version.iss"' in iss
    assert "AppPublisherURL=" in iss
    assert "AppSupportURL=" in iss
    assert "AppUpdatesURL=" in iss
    assert "AppContact=" in iss
    assert "VersionInfoCopyright=" in iss
    assert "CloseApplications=yes" in iss
    assert "AppMutex=JU-TANOfficeMutex" in iss
    assert "docs\\PRIVACY.md" in iss or "docs/PRIVACY.md" in iss
    assert "docs\\USER_GUIDE.md" in iss or "docs/USER_GUIDE.md" in iss
    assert "docs\\ADMIN_GUIDE.md" in iss or "docs/ADMIN_GUIDE.md" in iss
    assert "docs\\RELEASE_NOTES.md" in iss or "docs/RELEASE_NOTES.md" in iss
    assert "docs\\SECURITY.md" in iss or "docs/SECURITY.md" in iss
    assert r'Dokumentacija\Skrbniški vodič' in iss or "Dokumentacija/Skrbniški vodič" in iss
    assert r'Dokumentacija\Opombe ob izdaji' in iss or "Dokumentacija/Opombe ob izdaji" in iss
    assert r'Dokumentacija\Uporabniški vodič' in iss or "Dokumentacija/Uporabniški vodič" in iss
    assert r'Dokumentacija\Varnost' in iss or "Dokumentacija/Varnost" in iss

    version_iss = (ROOT / "packaging" / "version.iss").read_text(encoding="utf-8")
    assert f'MyAppVersion "{APP_VERSION}"' in version_iss
    assert APP_PUBLISHER_URL in version_iss
    assert f'MySchemaVersion "{SCHEMA_VERSION}"' in version_iss


def test_packaging_spec_includes_release_docs():
    spec = (ROOT / "packaging" / "ju-tan-office.spec").read_text(encoding="utf-8")
    for doc in (
        "PRIVACY.md",
        "INSTALL.md",
        "USER_GUIDE.md",
        "ADMIN_GUIDE.md",
        "RELEASE_NOTES.md",
        "SECURITY.md",
        "SIGNING.md",
    ):
        assert doc in spec


def test_install_md_sources_aligned():
    root = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
    assert root == docs


def test_no_stale_packaging_sha256sums():
    assert not (ROOT / "packaging" / "SHA256SUMS.txt").exists()
    build = (ROOT / "scripts" / "build_release.ps1").read_text(encoding="utf-8")
    assert "dist/SHA256SUMS.txt" in build


def test_changelog_aligned_with_app_version():
    text = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {APP_VERSION}" in text or f"## {APP_VERSION} GOLD" in text
    assert "## 1.0.1" not in text
    report = (ROOT / "docs" / "RELEASE_REPORT.md").read_text(encoding="utf-8")
    assert APP_VERSION in report
    assert f"SCHEMA_VERSION` = **{SCHEMA_VERSION}**" in report or f"SCHEMA {SCHEMA_VERSION}" in report
    cert = (ROOT / "docs" / "GOLD_CERT.md").read_text(encoding="utf-8")
    assert "schema v2" in cert.lower()


def test_signing_readiness_doc_present():
    path = ROOT / "docs" / "SIGNING.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "JU_TAN_PFX" in text
    assert "signtool" in text.lower()
    assert "RequireSigned" in text or "JU_TAN_REQUIRE_SIGNED" in text
    assert "SHA256SUMS" in text
    assert "JU-TAN-Office.exe" in text
    assert "JU-TAN-Office-Setup.exe" in text

    build = (ROOT / "scripts" / "build_release.ps1").read_text(encoding="utf-8")
    assert "AuthenticodeSigning.ps1" in build
    assert "Invoke-AuthenticodeSign" in build
    assert "Write-Checksums" in build
    assert "verify_release_signatures.ps1" in build
    # Build order: sign app EXE before portable / installer; checksums after setup signing
    assert build.index("Invoke-AuthenticodeSign -Path $appExe") < build.index(
        "Compress-Archive -Path $portable"
    )
    setup_sign_at = build.index("Invoke-AuthenticodeSign -Path $setup")
    assert "Write-Checksums" in build[setup_sign_at:]
    assert "verify_release_signatures.ps1" in build[setup_sign_at:]

    lib = (ROOT / "scripts" / "AuthenticodeSigning.ps1").read_text(encoding="utf-8")
    assert "Find-SignTool" in lib
    assert "JU_TAN_TIMESTAMP_URL" in lib
    assert "Get-JuTanTimestampUrl" in lib

    verify = (ROOT / "scripts" / "verify_release_signatures.ps1").read_text(encoding="utf-8")
    assert "Get-AuthenticodeSignature" in verify
    assert "RequireSigned" in verify
    assert "Publisher" in verify


def test_splash_branding_pixmap(qt_app):
    pix, fg = build_splash_pixmap("light")
    assert not pix.isNull()
    assert pix.width() >= 400
    assert pix.height() >= 200
    assert fg.isValid()

    dark_pix, dark_fg = build_splash_pixmap("dark")
    assert not dark_pix.isNull()
    assert dark_fg.isValid()


def test_docs_reference_privacy():
    for rel in ("docs/USER_GUIDE.md", "docs/INSTALL.md", "docs/SECURITY.md", "docs/RELEASE_NOTES.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "PRIVACY" in text or "zasebnost" in text.lower()
