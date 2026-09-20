"""Privacy-preserving, stable device identification."""

import hashlib
import os
import platform
import uuid


def _machine_material() -> str:
    parts = [platform.system(), platform.machine(), platform.node(), str(uuid.getnode())]
    if os.name == "nt":
        parts.append(os.environ.get("COMPUTERNAME", ""))
    else:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                with open(path, encoding="utf-8") as handle:
                    parts.append(handle.read().strip())
                break
            except OSError:
                continue
    return "|".join(part.strip().lower() for part in parts if part)


def device_fingerprint(product_salt: str = "ju-tan-office-v1") -> str:
    """Return a one-way device identifier; raw hardware data never leaves the PC."""
    material = f"{product_salt}|{_machine_material()}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()
