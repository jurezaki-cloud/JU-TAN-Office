"""Typed local state for the licensing subsystem."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class LicenseStatus(str, Enum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    DEVICE_LIMIT = "device_limit"


@dataclass(frozen=True)
class LicenseState:
    status: LicenseStatus = LicenseStatus.UNKNOWN
    license_id: str = ""
    company_name: str = ""
    device_id: str = ""
    activation_token: str = ""
    checked_at: str = ""
    valid_until: str = ""
    grace_until: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "LicenseState":
        allowed = {field.name for field in __import__("dataclasses").fields(cls)}
        clean = {key: item for key, item in value.items() if key in allowed}
        clean["status"] = LicenseStatus(clean.get("status", "unknown"))
        return cls(**clean)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value
