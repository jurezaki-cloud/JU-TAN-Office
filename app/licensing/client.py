"""Small HTTPS client for the JU-TAN licensing API."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class LicenseApiError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class LicenseApiClient:
    def __init__(self, base_url: str, timeout: float = 8.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        if urlparse(self.base_url).scheme != "https":
            raise ValueError("Licenčni API mora uporabljati HTTPS.")

    def _post(self, endpoint: str, payload: dict) -> dict:
        request = Request(
            f"{self.base_url}{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("error")
            except Exception:
                detail = None
            raise LicenseApiError(
                detail or "Licenčni strežnik je zahtevo zavrnil.",
                retryable=exc.code >= 500,
                status_code=exc.code,
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise LicenseApiError("Licenčni strežnik trenutno ni dosegljiv.", retryable=True) from exc

    def activate(self, license_key: str, device_id: str, app_version: str) -> dict:
        return self._post("/v1/licenses/activate", {
            "license_key": license_key.strip().upper(),
            "device_id": device_id,
            "app_version": app_version,
        })

    def validate(self, activation_token: str, device_id: str, app_version: str) -> dict:
        return self._post("/v1/licenses/validate", {
            "activation_token": activation_token,
            "device_id": device_id,
            "app_version": app_version,
        })

    def deactivate(self, activation_token: str, device_id: str) -> dict:
        return self._post("/v1/licenses/deactivate", {
            "activation_token": activation_token,
            "device_id": device_id,
        })
