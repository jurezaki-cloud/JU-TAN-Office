"""Backward-compatible access to the desktop application configuration.

New code should import from :mod:`app.core.config` or
:mod:`app.core.constants` directly.
"""

from app.core.config import *  # noqa: F401,F403
