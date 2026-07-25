from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.api.pagination import paginate
from app.api.schemas import AlertOut, Page
from app.models.orm import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_user)])


@router.get("", response_model=Page[AlertOut])
def list_alerts(
    device_id: str | None = Query(None, description="Filtra por sensor_id"),
    gas_type: str | None = Query(None, description="CH4 ou CO2"),
    status_: str | None = Query(None, alias="status", description="active ou resolved"),
    start: datetime | None = Query(None, description="started_at >= start"),
    end: datetime | None = Query(None, description="started_at <= end"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[AlertOut]:
    query = db.query(Alert)
    if device_id:
        query = query.filter(Alert.sensor_id == device_id)
    if gas_type:
        query = query.filter(Alert.gas_type == gas_type)
    if status_:
        query = query.filter(Alert.status == status_)
    if start:
        query = query.filter(Alert.started_at >= start)
    if end:
        query = query.filter(Alert.started_at <= end)
    query = query.order_by(Alert.started_at.desc())

    items, total = paginate(query, limit, offset)
    return Page(items=items, total=total, limit=limit, offset=offset)
