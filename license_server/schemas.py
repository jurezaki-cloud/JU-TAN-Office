from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ActivationRequest(BaseModel):
    license_key: str = Field(min_length=12, max_length=80)
    company_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    installation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    app_version: str = Field(max_length=40)
    platform: str = Field(max_length=80)


class HeartbeatRequest(BaseModel):
    activation_id: str
    installation_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    app_version: str = Field(max_length=40)
    platform: str = Field(max_length=80)


class DeactivationRequest(BaseModel):
    activation_id: str
    installation_id: str = Field(pattern=r"^[a-f0-9]{64}$")


class LicenseCreateRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    plan: str = Field(default="business", max_length=40)
    max_devices: int = Field(default=1, ge=1, le=100)
    valid_until: datetime


class LicenseStatusRequest(BaseModel):
    status: Literal["active", "suspended", "revoked"]
