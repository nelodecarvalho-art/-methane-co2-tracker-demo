from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.api.pagination import paginate
from app.api.schemas import DeviceOut, Page
from app.models.orm import Sensor

router = APIRouter(prefix="/devices", tags=["devices"], dependencies=[Depends(require_user)])


@router.get("", response_model=Page[DeviceOut])
def list_devices(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[DeviceOut]:
    query = db.query(Sensor).order_by(Sensor.sensor_id)
    items, total = paginate(query, limit, offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{sensor_id}", response_model=DeviceOut)
def get_device(sensor_id: str, db: Session = Depends(get_db)) -> DeviceOut:
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).one_or_none()
    if sensor is None:
        raise HTTPException(status_code=404, detail="dispositivo não encontrado")
    return sensor
