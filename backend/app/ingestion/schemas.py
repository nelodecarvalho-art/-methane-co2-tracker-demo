from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, field_validator


class ReadingIn(BaseModel):
    time: datetime
    sensor_id: str
    gas_type: Literal["CH4", "CO2"]
    concentration_ppm: float
    temperature_c: float
    battery_pct: float

    @field_validator("concentration_ppm")
    @classmethod
    def ppm_must_be_sane(cls, v: float) -> float:
        # uint32 no proto cobre a faixa toda; acima disso o payload já veio
        # corrompido antes mesmo do parse binário falhar.
        if v < 0 or v > 1_000_000:
            raise ValueError(f"concentration_ppm fora da faixa esperada: {v}")
        return v

    @field_validator("battery_pct")
    @classmethod
    def battery_in_range(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError(f"battery_pct fora de 0-100: {v}")
        return v

    @field_validator("time")
    @classmethod
    def time_not_absurd(cls, v: datetime) -> datetime:
        # Guarda contra timestamp=0 ou relógio de sensor sem sync (RTC
        # zerado é uma falha comum de campo, não deve virar leitura de 1970).
        now = datetime.now(timezone.utc)
        if v.year < 2020 or v > now:
            raise ValueError(f"timestamp implausível: {v.isoformat()}")
        return v
