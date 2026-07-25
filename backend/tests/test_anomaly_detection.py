"""
Script standalone (sem pytest). Requer TimescaleDB rodando (docker-compose up
timescaledb) e as migrations já aplicadas (alembic upgrade head, dentro de
backend/). Roda: python tests/test_anomaly_detection.py
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.anomaly.detector import is_anomaly  # noqa: E402
from app.db.session import SessionLocal, settings  # noqa: E402
from app.models.orm import Reading, Sensor  # noqa: E402

TEST_SENSOR_ID = "test-sensor-anomaly-detection"


def _cleanup(db) -> None:
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.commit()


def _insert_reading(db, t: datetime, ppm: float, temp: float, battery: float) -> None:
    db.add(
        Reading(
            time=t,
            sensor_id=TEST_SENSOR_ID,
            gas_type="CH4",
            concentration_ppm=ppm,
            temperature_c=temp,
            battery_pct=battery,
        )
    )
    db.commit()


def main() -> None:
    db = SessionLocal()
    random.seed(42)

    try:
        _cleanup(db)
        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=65002,
                asset_id="test-asset",
                name="Sensor de teste - detecção de anomalia",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        base_time = datetime.now(timezone.utc) - timedelta(hours=2)

        # Sem histórico mínimo ainda -> não classifica (False), mesmo com
        # leitura fora do padrão.
        first_time = base_time
        _insert_reading(db, first_time, ppm=999.0, temp=200.0, battery=1.0)
        assert is_anomaly(db, TEST_SENSOR_ID, "CH4", first_time) is False, (
            "não deveria classificar sem histórico mínimo"
        )

        # Histórico estável: leituras normais em torno de um valor de base,
        # com ruído pequeno — simula operação normal do sensor.
        t = first_time
        for _ in range(settings.anomaly_min_history + 20):
            t += timedelta(seconds=30)
            ppm = 80.0 + random.uniform(-3, 3)
            temp = 25.0 + random.uniform(-0.5, 0.5)
            battery = 90.0 + random.uniform(-1, 1)
            _insert_reading(db, t, ppm=ppm, temp=temp, battery=battery)

        normal_time = t
        assert is_anomaly(db, TEST_SENSOR_ID, "CH4", normal_time) is False, (
            "leitura dentro do padrão não deveria ser marcada como anomalia"
        )

        # Leitura claramente fora do padrão (pico isolado, bem acima do
        # ruído normal) -> deve ser marcada.
        anomaly_time = t + timedelta(seconds=30)
        _insert_reading(db, anomaly_time, ppm=850.0, temp=60.0, battery=90.0)
        assert is_anomaly(db, TEST_SENSOR_ID, "CH4", anomaly_time) is True, (
            "leitura fora do padrão deveria ser marcada como anomalia"
        )

        print("OK: detecção de anomalia (cold start, leitura normal, leitura fora do padrão)")
    finally:
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
