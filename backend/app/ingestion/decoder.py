from datetime import datetime, timezone

from google.protobuf.message import DecodeError
from sqlalchemy.orm import Session

from app.ingestion.generated import sensor_reading_pb2 as pb
from app.models.orm import Sensor


class DecodeFailure(Exception):
    pass


def decode_reading(db: Session, raw: bytes) -> dict:
    """Decodifica bytes Protobuf crus vindos do MQTT em um dict pronto pra
    validação Pydantic. Traduz sensor_id numérico curto -> sensor_id string
    via lookup na tabela `sensors`. Levanta DecodeFailure em qualquer
    problema (bytes corrompidos, sensor desconhecido) — quem chama decide o
    que fazer (logar e descartar, não deixar propagar e derrubar o consumer).
    """
    msg = pb.SensorReading()
    try:
        msg.ParseFromString(raw)
    except DecodeError as exc:
        raise DecodeFailure(f"protobuf malformado: {exc}") from exc

    sensor = (
        db.query(Sensor).filter(Sensor.sensor_id_short == msg.sensor_id).one_or_none()
    )
    if sensor is None:
        raise DecodeFailure(f"sensor_id_short desconhecido: {msg.sensor_id}")

    return {
        "time": datetime.fromtimestamp(msg.timestamp, tz=timezone.utc),
        "sensor_id": sensor.sensor_id,
        "gas_type": pb.GasType.Name(msg.gas_type),
        "concentration_ppm": float(msg.concentration_ppm),
        "temperature_c": msg.temperature_c_x10 / 10.0,
        "battery_pct": float(msg.battery_pct),
    }
