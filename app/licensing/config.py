import os


def _enabled(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


LICENSE_REQUIRED = _enabled(os.environ.get("JU_TAN_LICENSE_REQUIRED", "0"))
LICENSE_SERVER_URL = os.environ.get(
    "JU_TAN_LICENSE_SERVER_URL", "https://license.ju-tan.com"
).rstrip("/")

# Set JU_TAN_LICENSE_PUBLIC_KEY during development. For a production build,
# replace this empty value with the server's Ed25519 public key. Never embed
# the private signing key in the desktop application.
DEFAULT_LICENSE_PUBLIC_KEY = ""
LICENSE_PUBLIC_KEY = os.environ.get(
    "JU_TAN_LICENSE_PUBLIC_KEY", DEFAULT_LICENSE_PUBLIC_KEY
).strip()
