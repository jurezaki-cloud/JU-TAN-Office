import base64
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.licensing.models import LicenseStatus
from app.licensing.storage import LicenseStorage
from app.licensing.verifier import LicenseVerifier, canonical_json
from license_server.database import LicenseDatabase
from license_server.security import generate_signing_keys
from license_server.service import LicenseError, LicenseService


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        public = self.private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self.public = base64.b64encode(public).decode("ascii")
        self.now = datetime(2026, 9, 20, tzinfo=timezone.utc)

    def certificate(self, **changes):
        claims = {
            "installation_id": "a" * 64,
            "status": "active",
            "valid_until": "2027-09-20T00:00:00Z",
            "offline_warning_at": "2026-10-04T00:00:00Z",
            "offline_until": "2026-10-11T00:00:00Z",
        }
        claims.update(changes)
        signature = self.private.sign(canonical_json(claims))
        return {
            "claims": claims,
            "signature": base64.b64encode(signature).decode("ascii"),
        }

    def test_accepts_valid_signed_certificate(self):
        state = LicenseVerifier(self.public, now=lambda: self.now).verify(
            self.certificate(), "a" * 64
        )
        self.assertEqual(state.status, LicenseStatus.ACTIVE)

    def test_rejects_tampered_claims(self):
        certificate = self.certificate()
        certificate["claims"]["plan"] = "unlimited"
        state = LicenseVerifier(self.public, now=lambda: self.now).verify(
            certificate, "a" * 64
        )
        self.assertEqual(state.status, LicenseStatus.INVALID)

    def test_rejects_certificate_copied_to_another_installation(self):
        state = LicenseVerifier(self.public, now=lambda: self.now).verify(
            self.certificate(), "b" * 64
        )
        self.assertEqual(state.status, LicenseStatus.INVALID)

    def test_storage_recovers_from_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activation.json"
            path.write_text("not-json", encoding="utf-8")
            self.assertIsNone(LicenseStorage(path).load())


class LicenseServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = LicenseDatabase(Path(self.temp.name) / "licenses.db")
        self.database.initialize()
        self.private, self.public = generate_signing_keys()
        self.now = datetime(2026, 9, 20, tzinfo=timezone.utc)
        self.service = LicenseService(
            self.database, self.private, "test-pepper", now=lambda: self.now
        )
        created = self.service.create_license(
            "Test d.o.o.", "office@example.com", "business", 1,
            self.now + timedelta(days=365),
        )
        self.key = created["license_key"]

    def tearDown(self):
        self.temp.cleanup()

    def request(self, installation="a" * 64):
        return SimpleNamespace(
            license_key=self.key, company_name="Test d.o.o.",
            email="office@example.com", installation_id=installation,
            app_version="0.2.0", platform="Windows",
        )

    def test_activate_and_verify_certificate(self):
        certificate = self.service.activate(self.request())
        state = LicenseVerifier(self.public, now=lambda: self.now).verify(
            certificate, "a" * 64
        )
        self.assertEqual(state.status, LicenseStatus.ACTIVE)

    def test_device_limit_is_enforced(self):
        self.service.activate(self.request("a" * 64))
        with self.assertRaises(LicenseError):
            self.service.activate(self.request("b" * 64))

    def test_deactivated_seat_can_be_reused(self):
        first = self.service.activate(self.request("a" * 64))
        self.service.deactivate(first["claims"]["activation_id"], "a" * 64)
        second = self.service.activate(self.request("b" * 64))
        self.assertEqual(second["claims"]["installation_id"], "b" * 64)

    def test_revoked_license_cannot_refresh(self):
        certificate = self.service.activate(self.request())
        activation_id = certificate["claims"]["activation_id"]
        self.service.set_license_status(certificate["claims"]["license_id"], "revoked")
        heartbeat = SimpleNamespace(
            activation_id=activation_id, installation_id="a" * 64,
            app_version="0.2.0", platform="Windows",
        )
        with self.assertRaises(LicenseError):
            self.service.heartbeat(heartbeat)


if __name__ == "__main__":
    unittest.main()
