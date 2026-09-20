import base64
import json
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.licensing.models import LicenseState, LicenseStatus, parse_utc


def canonical_json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class LicenseVerifier:
    def __init__(self, public_key_base64, now=None):
        self.public_key_base64 = public_key_base64
        self.now = now or (lambda: datetime.now(timezone.utc))

    def verify(self, certificate, expected_installation_id):
        if not certificate:
            return LicenseState(LicenseStatus.NOT_ACTIVATED, "Program ni aktiviran.")
        try:
            claims = certificate["claims"]
            signature = base64.b64decode(certificate["signature"], validate=True)
            public_bytes = base64.b64decode(self.public_key_base64, validate=True)
            Ed25519PublicKey.from_public_bytes(public_bytes).verify(
                signature, canonical_json(claims)
            )
        except (KeyError, TypeError, ValueError, InvalidSignature):
            return LicenseState(LicenseStatus.INVALID, "Licenčno potrdilo ni veljavno.")

        if claims.get("installation_id") != expected_installation_id:
            return LicenseState(
                LicenseStatus.INVALID, "Licenca pripada drugi namestitvi."
            )
        if claims.get("status") == "revoked":
            return LicenseState(LicenseStatus.REVOKED, "Licenca je bila preklicana.")

        current = self.now()
        valid_until = parse_utc(claims.get("valid_until"))
        offline_until = parse_utc(claims.get("offline_until"))
        if not valid_until or current > valid_until:
            return LicenseState(LicenseStatus.EXPIRED, "Licenca je potekla.", claims)
        if not offline_until or current > offline_until:
            return LicenseState(
                LicenseStatus.EXPIRED,
                "Za nadaljevanje je potrebno spletno preverjanje licence.",
                claims,
            )
        warning_at = parse_utc(claims.get("offline_warning_at"))
        if warning_at and current > warning_at:
            return LicenseState(
                LicenseStatus.GRACE_PERIOD,
                "Licenco bo kmalu treba preveriti prek interneta.",
                claims,
            )
        return LicenseState(LicenseStatus.ACTIVE, "Licenca je aktivna.", claims)
