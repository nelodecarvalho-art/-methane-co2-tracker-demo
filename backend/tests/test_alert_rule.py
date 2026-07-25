"""
Script standalone (sem pytest). Requer TimescaleDB rodando (docker-compose up
timescaledb) e as migrations já aplicadas (alembic upgrade head, dentro de
backend/). Roda: python tests/test_alert_rule.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.alerts.rules import evaluate_alert  # noqa: E402
from app.db.session import SessionLocal, settings  # noqa: E402
from app.models.orm import Alert, Reading, Sensor  # noqa: E402

TEST_SENSOR_ID = "test-sensor-alert-rule"


def _cleanup(db) -> None:
    db.query(Alert).filter(Alert.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.commit()


def main() -> None:
    db = SessionLocal()
    threshold = settings.alert_thresholds_ppm["CH4"]
    window = settings.alert_window_seconds

    try:
        _cleanup(db)

        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=65001,
                asset_id="test-asset",
                name="Sensor de teste - regra de alerta",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        base_time = datetime.now(timezone.utc)

        # Janela cheia, todas as leituras acima do threshold -> deve abrir alerta.
        for i in range(5):
            t = base_time - timedelta(seconds=window) + timedelta(seconds=i * (window / 4))
            db.add(
                Reading(
                    time=t,
                    sensor_id=TEST_SENSOR_ID,
                    gas_type="CH4",
                    concentration_ppm=threshold + 50,
                )
            )
        db.commit()
        evaluate_alert(db, TEST_SENSOR_ID, "CH4", base_time)

        active = (
            db.query(Alert)
            .filter(Alert.sensor_id == TEST_SENSOR_ID, Alert.status == "active")
            .one_or_none()
        )
        assert active is not None, "alerta deveria ter aberto com janela toda acima do threshold"
        assert active.max_ppm == threshold + 50

        # Leitura abaixo do threshold -> deve fechar o alerta ativo.
        below_time = base_time + timedelta(seconds=1)
        db.add(
            Reading(
                time=below_time,
                sensor_id=TEST_SENSOR_ID,
                gas_type="CH4",
                concentration_ppm=threshold - 10,
            )
        )
        db.commit()
        evaluate_alert(db, TEST_SENSOR_ID, "CH4", below_time)

        db.refresh(active)
        assert active.status == "resolved", "alerta deveria ter fechado ao cair abaixo do threshold"
        assert active.ended_at is not None

        # Janela sem cobertura completa (poucas leituras recentes, sem
        # histórico voltando até a borda da janela) -> NÃO deve abrir alerta,
        # mesmo com leitura pontual acima do threshold.
        _cleanup(db)
        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=65001,
                asset_id="test-asset",
                name="Sensor de teste - regra de alerta",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        lone_time = datetime.now(timezone.utc)
        db.add(
            Reading(
                time=lone_time,
                sensor_id=TEST_SENSOR_ID,
                gas_type="CH4",
                concentration_ppm=threshold + 999,
            )
        )
        db.commit()
        evaluate_alert(db, TEST_SENSOR_ID, "CH4", lone_time)
        no_alert = (
            db.query(Alert)
            .filter(Alert.sensor_id == TEST_SENSOR_ID, Alert.status == "active")
            .one_or_none()
        )
        assert no_alert is None, "não deveria abrir alerta sem cobertura completa da janela"

        print("OK: regra de alerta sustentado (abre, fecha, e não dispara sem janela completa)")
    finally:
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
