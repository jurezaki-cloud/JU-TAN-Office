from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class LicenseStatus(str, Enum):
    NOT_ACTIVATED = "not_activated"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"
    SERVER_UNAVAILABLE = "server_unavailable"


@dataclass(frozen=True)
class LicenseState:
    status: LicenseStatus
    message: str
    claims: dict | None = None

    @property
    def permits_use(self):
        return self.status in {
            LicenseStatus.ACTIVE,
            LicenseStatus.GRACE_PERIOD,
            LicenseStatus.SERVER_UNAVAILABLE,
        }


def parse_utc(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
