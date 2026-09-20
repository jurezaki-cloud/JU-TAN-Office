import os
from pathlib import Path


DATABASE_PATH = Path(os.environ.get("JUTAN_LICENSE_DB", "license_server/data/licenses.db"))
SIGNING_KEY = os.environ.get("JUTAN_LICENSE_SIGNING_KEY", "").strip()
LICENSE_PEPPER = os.environ.get("JUTAN_LICENSE_PEPPER", "").strip()
ADMIN_TOKEN = os.environ.get("JUTAN_LICENSE_ADMIN_TOKEN", "").strip()
OFFLINE_WARNING_DAYS = int(os.environ.get("JUTAN_OFFLINE_WARNING_DAYS", "14"))
OFFLINE_LIMIT_DAYS = int(os.environ.get("JUTAN_OFFLINE_LIMIT_DAYS", "21"))


def validate_production_config():
    missing = [
        name for name, value in (
            ("JUTAN_LICENSE_SIGNING_KEY", SIGNING_KEY),
            ("JUTAN_LICENSE_PEPPER", LICENSE_PEPPER),
            ("JUTAN_LICENSE_ADMIN_TOKEN", ADMIN_TOKEN),
        ) if not value
    ]
    if missing:
        raise RuntimeError("Manjkajo obvezne nastavitve: " + ", ".join(missing))
