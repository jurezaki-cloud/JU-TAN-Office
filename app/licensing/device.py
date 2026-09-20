"""Create a stable pseudonymous installation identifier.

Raw hardware identifiers never leave the device. The random installation ID
also prevents JU-TAN from correlating a device across unrelated products.
"""

import hashlib
import json
import platform
import secrets

from app.core.constants import LICENSE_DIR


INSTALLATION_FILE = LICENSE_DIR / "installation.json"


def _load_or_create_salt(path=INSTALLATION_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("salt"):
            return payload["salt"]
    except (OSError, ValueError, TypeError):
        pass
    salt = secrets.token_hex(32)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"salt": salt}), encoding="utf-8")
    temporary.replace(path)
    return salt


def installation_id(path=INSTALLATION_FILE):
    salt = _load_or_create_salt(path)
    material = "|".join((platform.system(), platform.machine(), platform.node()))
    return hashlib.sha256(f"{salt}|{material}".encode("utf-8")).hexdigest()
