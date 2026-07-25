from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.api.pagination import paginate
from app.api.schemas import Page, ReadingOut
from app.models.orm import Reading

router = APIRouter(prefix="/readings", tags=["readings"], dependencies=[Depends(require_user)])


@router.get("", response_model=Page[ReadingOut])
def list_readings(
    device_id: str | None = Query(None, description="Filtra por sensor_id"),
    gas_type: str | None = Query(None, description="CH4 ou CO2"),
    start: datetime | None = Query(None, description="time >= start"),
    end: datetime | None = Query(None, description="time <= end"),
    is_anomaly: bool | None = Query(None, description="Filtra por leituras marcadas como anômalas"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[ReadingOut]:
    query = db.query(Reading)
    if device_id:
        query = query.filter(Reading.sensor_id == device_id)
    if gas_type:
        query = query.filter(Reading.gas_type == gas_type)
    if start:
        query = query.filter(Reading.time >= start)
    if end:
        query = query.filter(Reading.time <= end)
    if is_anomaly is not None:
        query = query.filter(Reading.is_anomaly == is_anomaly)
    query = query.order_by(Reading.time.desc())

    items, total = paginate(query, limit, offset)
    return Page(items=items, total=total, limit=limit, offset=offset)
