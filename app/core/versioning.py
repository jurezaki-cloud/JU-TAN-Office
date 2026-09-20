"""Version source-of-truth helpers.

``APP_VERSION`` in ``app.core.constants`` is authoritative. Packaging metadata
(Version.txt, file_version_info.txt, installer.iss) must match it.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.constants import APP_VERSION, BASE_DIR

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

_VERSION_LINE_RE = re.compile(r"^Version:\s*(\d+\.\d+\.\d+)\b", re.MULTILINE)
_FILE_VERSION_RE = re.compile(
    r"StringStruct\(u'(?:File|Product)Version',\s*u'(\d+\.\d+\.\d+)'\)"
)
_FILEVERS_RE = re.compile(r"(?:filevers|prodvers)=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)")
_ISS_DEFINE_RE = re.compile(r'#define\s+MyAppVersion\s+"(\d+\.\d+\.\d+)"')
_ISS_VERSION_INFO_RE = re.compile(r"^VersionInfoVersion=(\d+\.\d+\.\d+)\s*$", re.MULTILINE)


class VersionError(ValueError):
    """Version parse or drift error."""


def parse_semver(text: str) -> tuple[int, int, int]:
    """Parse strict ``MAJOR.MINOR.PATCH`` (no suffixes)."""
    raw = (text or "").strip()
    match = SEMVER_RE.fullmatch(raw)
    if not match:
        raise VersionError(f"Malformed version: {text!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_semver(parts: tuple[int, int, int]) -> str:
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def app_version() -> str:
    """Return authoritative application version."""
    parse_semver(APP_VERSION)
    return APP_VERSION


def version_tuple_for_win32(version: str | None = None) -> tuple[int, int, int, int]:
    major, minor, patch = parse_semver(version or APP_VERSION)
    return major, minor, patch, 0


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise VersionError(f"Missing version metadata file: {path}")
    return path.read_text(encoding="utf-8")


def collect_version_sources(root: Path | None = None) -> dict[str, str]:
    """Collect declared versions from packaging / release metadata files."""
    base = root or BASE_DIR
    sources: dict[str, str] = {"APP_VERSION": APP_VERSION}

    for label, path in (
        ("Version.txt", base / "Version.txt"),
        ("packaging/Version.txt", base / "packaging" / "Version.txt"),
    ):
        text = _read_text(path)
        match = _VERSION_LINE_RE.search(text)
        if not match:
            raise VersionError(f"No Version: line in {path}")
        sources[label] = match.group(1)

    fvi = _read_text(base / "packaging" / "file_version_info.txt")
    string_versions = set(_FILE_VERSION_RE.findall(fvi))
    if string_versions != {APP_VERSION} and len(string_versions) != 1:
        # Still record something for drift reporting
        sources["file_version_info.txt/strings"] = ",".join(sorted(string_versions)) or "<missing>"
    elif string_versions:
        sources["file_version_info.txt"] = next(iter(string_versions))
    else:
        raise VersionError("file_version_info.txt missing FileVersion/ProductVersion")

    expected_tuple = version_tuple_for_win32(APP_VERSION)
    for match in _FILEVERS_RE.finditer(fvi):
        found = tuple(int(x) for x in match.groups())
        if found != expected_tuple:
            sources["file_version_info.txt/filevers"] = ".".join(str(x) for x in found[:3])

    iss = _read_text(base / "packaging" / "installer.iss")
    define = _ISS_DEFINE_RE.search(iss)
    if not define:
        raise VersionError("installer.iss missing MyAppVersion define")
    sources["installer.iss/MyAppVersion"] = define.group(1)
    info = _ISS_VERSION_INFO_RE.search(iss)
    if info:
        sources["installer.iss/VersionInfoVersion"] = info.group(1)

    return sources


def detect_version_drift(root: Path | None = None) -> list[str]:
    """Return human-readable drift findings (empty if consistent)."""
    expected = app_version()
    sources = collect_version_sources(root)
    problems: list[str] = []
    for name, value in sources.items():
        if name == "APP_VERSION":
            continue
        # Normalize dotted triples only
        candidate = value.split(",")[0].strip()
        if candidate != expected:
            problems.append(f"{name}={value!r} != APP_VERSION={expected!r}")
    return problems


def assert_version_sources_consistent(root: Path | None = None) -> str:
    """Fail closed if any packaging version disagrees with APP_VERSION."""
    problems = detect_version_drift(root)
    if problems:
        raise VersionError("Version source drift detected:\n- " + "\n- ".join(problems))
    return app_version()


def render_file_version_info(version: str | None = None) -> str:
    ver = version or APP_VERSION
    major, minor, patch, build = version_tuple_for_win32(ver)
    return f"""# UTF-8
#
# PyInstaller version resource for JU-TAN-Office.exe
# GENERATED from APP_VERSION — do not edit by hand; run scripts/sync_version.py
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'JU-TAN Studio'),
        StringStruct(u'FileDescription', u'JU-TAN Office Enterprise'),
        StringStruct(u'FileVersion', u'{ver}'),
        StringStruct(u'InternalName', u'JU-TAN-Office'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2026 JU-TAN Studio'),
        StringStruct(u'OriginalFilename', u'JU-TAN-Office.exe'),
        StringStruct(u'ProductName', u'JU-TAN Office Enterprise'),
        StringStruct(u'ProductVersion', u'{ver}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def patch_version_txt(text: str, version: str | None = None) -> str:
    ver = version or APP_VERSION
    if not _VERSION_LINE_RE.search(text):
        raise VersionError("Version.txt missing Version: line")
    return _VERSION_LINE_RE.sub(f"Version: {ver} GOLD", text, count=1)


def patch_installer_iss(text: str, version: str | None = None) -> str:
    ver = version or APP_VERSION
    if not _ISS_DEFINE_RE.search(text):
        raise VersionError("installer.iss missing MyAppVersion")
    out = _ISS_DEFINE_RE.sub(f'#define MyAppVersion "{ver}"', text, count=1)
    if _ISS_VERSION_INFO_RE.search(out):
        out = _ISS_VERSION_INFO_RE.sub(f"VersionInfoVersion={ver}", out, count=1)
    return out


def write_version_metadata(root: Path | None = None) -> str:
    """Regenerate packaging version fields from APP_VERSION."""
    base = root or BASE_DIR
    ver = app_version()

    fvi_path = base / "packaging" / "file_version_info.txt"
    fvi_path.write_text(render_file_version_info(ver), encoding="utf-8")

    for path in (base / "Version.txt", base / "packaging" / "Version.txt"):
        path.write_text(patch_version_txt(_read_text(path), ver), encoding="utf-8")

    iss_path = base / "packaging" / "installer.iss"
    iss_path.write_text(patch_installer_iss(_read_text(iss_path), ver), encoding="utf-8")

    assert_version_sources_consistent(base)
    return ver
