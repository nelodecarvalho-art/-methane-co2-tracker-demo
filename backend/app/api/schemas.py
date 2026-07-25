from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    sensor_id: str
    gas_type: str
    concentration_ppm: float
    temperature_c: float | None
    battery_pct: float | None
    is_anomaly: bool


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sensor_id: str
    sensor_id_short: int
    asset_id: str
    name: str
    location_desc: str | None
    lat: float | None
    lon: float | None
    installed_at: datetime
    status: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: str
    gas_type: str
    started_at: datetime
    ended_at: datetime | None
    max_ppm: float
    status: str
    notified_at: datetime | None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
