import hmac

from fastapi import Depends, FastAPI, Header, HTTPException

from license_server import config
from license_server.database import LicenseDatabase
from license_server.schemas import (
    ActivationRequest, DeactivationRequest, HeartbeatRequest, LicenseCreateRequest,
    LicenseStatusRequest,
)
from license_server.service import LicenseError, LicenseService


config.validate_production_config()
database = LicenseDatabase()
database.initialize()
service = LicenseService(
    database, config.SIGNING_KEY, config.LICENSE_PEPPER,
    config.OFFLINE_WARNING_DAYS, config.OFFLINE_LIMIT_DAYS,
)
app = FastAPI(title="JU-TAN License & Control Center", version="1.0.0")


def require_admin(authorization: str = Header(default="")):
    supplied = authorization.removeprefix("Bearer ").strip()
    if not supplied or not hmac.compare_digest(supplied, config.ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Neveljavna skrbniška prijava.")


def call(action):
    try:
        return action()
    except LicenseError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/activations")
def activate(request: ActivationRequest):
    return {"certificate": call(lambda: service.activate(request))}


@app.post("/v1/heartbeat")
def heartbeat(request: HeartbeatRequest):
    return {"certificate": call(lambda: service.heartbeat(request))}


@app.post("/v1/activations/deactivate")
def deactivate(request: DeactivationRequest):
    call(lambda: service.deactivate(request.activation_id, request.installation_id))
    return {"ok": True}


@app.post("/v1/admin/licenses", dependencies=[Depends(require_admin)])
def create_license(request: LicenseCreateRequest):
    return service.create_license(
        request.company_name, request.email, request.plan,
        request.max_devices, request.valid_until,
    )


@app.get("/v1/admin/licenses", dependencies=[Depends(require_admin)])
def list_licenses():
    return {"licenses": service.list_licenses()}


@app.get("/v1/admin/licenses/{license_id}/activations", dependencies=[Depends(require_admin)])
def list_activations(license_id: str):
    return {"activations": service.list_activations(license_id)}


@app.patch("/v1/admin/licenses/{license_id}", dependencies=[Depends(require_admin)])
def update_license(license_id: str, request: LicenseStatusRequest):
    call(lambda: service.set_license_status(license_id, request.status))
    return {"ok": True}
