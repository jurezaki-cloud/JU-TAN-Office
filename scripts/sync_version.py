#!/usr/bin/env python3
"""Sync / validate packaging version metadata from APP_VERSION (SSOT)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.versioning import (  # noqa: E402
    VersionError,
    assert_version_sources_consistent,
    detect_version_drift,
    write_version_metadata,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Fail if packaging versions disagree with APP_VERSION",
    )
    group.add_argument(
        "--write",
        action="store_true",
        help="Rewrite packaging version metadata from APP_VERSION",
    )
    args = parser.parse_args(argv)

    try:
        if args.write:
            ver = write_version_metadata(ROOT)
            print(f"Synced packaging metadata to APP_VERSION={ver}")
            return 0
        ver = assert_version_sources_consistent(ROOT)
        print(f"Version sources OK: APP_VERSION={ver}")
        return 0
    except VersionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        for item in detect_version_drift(ROOT):
            print(f"  - {item}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
