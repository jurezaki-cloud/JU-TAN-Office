"""Resolve bundled documentation paths (dev tree or installed/portable root)."""

from __future__ import annotations

from pathlib import Path

from app.core.constants import BASE_DIR
from app.core.deploy_paths import install_root


def resolve_doc(*parts: str) -> Path | None:
    """Return first existing documentation file under install/docs or repo docs."""
    roots = (
        install_root() / "docs",
        install_root(),
        BASE_DIR / "docs",
        BASE_DIR,
    )
    for root in roots:
        candidate = root.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return None


def privacy_policy_path() -> Path | None:
    return resolve_doc("PRIVACY.md")
