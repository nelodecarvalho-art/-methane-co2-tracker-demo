"""
Script standalone (sem pytest). Requer TimescaleDB rodando (docker-compose up
timescaledb) e as migrations já aplicadas (alembic upgrade head, dentro de
backend/). Roda: python tests/test_db_connection.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.orm import Sensor  # noqa: E402


def main() -> None:
    db = SessionLocal()
    test_sensor_id = "test-sensor-passo1"
    try:
        db.query(Sensor).filter(Sensor.sensor_id == test_sensor_id).delete()
        db.commit()

        sensor = Sensor(
            sensor_id=test_sensor_id,
            sensor_id_short=65000,
            asset_id="test-asset",
            name="Sensor de teste - Passo 1",
            installed_at=datetime.now(timezone.utc),
        )
        db.add(sensor)
        db.commit()

        fetched = db.query(Sensor).filter(Sensor.sensor_id == test_sensor_id).one()
        assert fetched.sensor_id == test_sensor_id
        assert fetched.sensor_id_short == 65000
        assert fetched.status == "active"

        print("OK: conexao, insert e query no TimescaleDB funcionando")
    finally:
        db.query(Sensor).filter(Sensor.sensor_id == test_sensor_id).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    main()
