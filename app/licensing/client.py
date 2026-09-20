import json
import platform
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from app import __version__
from app.licensing.device import installation_id
from app.licensing.models import LicenseState, LicenseStatus, parse_utc
from app.licensing.storage import LicenseStorage


class LicenseServiceError(RuntimeError):
    pass


class LicenseClient:
    def __init__(self, base_url, verifier, storage=None, timeout=8):
        self.base_url = base_url.rstrip("/")
        self.verifier = verifier
        self.storage = storage or LicenseStorage()
        self.timeout = timeout

    def local_status(self):
        return self.verifier.verify(self.storage.load(), installation_id())

    def activate(self, license_key, company_name, email):
        certificate = self._post("/v1/activations", {
            "license_key": license_key.strip(),
            "company_name": company_name.strip(),
            "email": email.strip(),
            "installation_id": installation_id(),
            "app_version": __version__,
            "platform": platform.system(),
        })["certificate"]
        state = self.verifier.verify(certificate, installation_id())
        if not state.permits_use:
            raise LicenseServiceError(state.message)
        self.storage.save(certificate)
        return state

    def refresh(self):
        current = self.storage.load()
        if not current:
            return LicenseState(LicenseStatus.NOT_ACTIVATED, "Program ni aktiviran.")
        local = self.local_status()
        issued_at = parse_utc(current.get("claims", {}).get("issued_at"))
        if (
            local.permits_use
            and issued_at
            and datetime.now(timezone.utc) - issued_at < timedelta(hours=24)
        ):
            return local
        try:
            response = self._post("/v1/heartbeat", {
                "activation_id": current["claims"]["activation_id"],
                "installation_id": installation_id(),
                "app_version": __version__,
                "platform": platform.system(),
            })
            certificate = response["certificate"]
            state = self.verifier.verify(certificate, installation_id())
            if state.permits_use:
                self.storage.save(certificate)
            return state
        except LicenseServiceError:
            if local.permits_use:
                return LicenseState(
                    LicenseStatus.SERVER_UNAVAILABLE,
                    "Strežnik trenutno ni dosegljiv; uporabljena je veljavna lokalna licenca.",
                    local.claims,
                )
            return local

    def deactivate(self):
        current = self.storage.load()
        if current:
            self._post("/v1/activations/deactivate", {
                "activation_id": current["claims"]["activation_id"],
                "installation_id": installation_id(),
            })
        self.storage.clear()

    def _post(self, path, payload):
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "JU-TAN-Office"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                detail = json.loads(error.read().decode("utf-8")).get("detail")
            except (ValueError, AttributeError):
                detail = None
            raise LicenseServiceError(detail or "Aktivacija ni uspela.") from error
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            raise LicenseServiceError("Licenčni strežnik ni dosegljiv.") from error
