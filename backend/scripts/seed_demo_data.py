"""
Popula o banco com dados 100% sintéticos para o ambiente de DEMONSTRAÇÃO
PÚBLICA (LinkedIn/vitrine) — nunca dado real de cliente. Idempotente: apaga
qualquer dado de demo anterior (sensor_id começando com "demo-") antes de
recriar, então pode ser rodado de novo sem duplicar.

Roda: python backend/scripts/seed_demo_data.py
(Do host, sem estar dentro do container: DB_HOST=localhost python ...)
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.orm import Alert, Reading, Sensor  # noqa: E402

DEMO_SENSOR_PREFIX = "demo-"

SENSORS = [
    {
        "sensor_id": "demo-sensor-ch4-01",
        "sensor_id_short": 90001,
        "asset_id": "demo-planta-fake-1",
        "name": "[DEMO] Sensor CH4 — Unidade Fictícia Norte",
        "location_desc": "Dado sintético para demonstração — não é uma instalação real",
        "gas_type": "CH4",
        "baseline_ppm": 95.0,
        "noise_ppm": 8.0,
    },
    {
        "sensor_id": "demo-sensor-co2-01",
        "sensor_id_short": 90002,
        "asset_id": "demo-planta-fake-1",
        "name": "[DEMO] Sensor CO2 — Unidade Fictícia Norte",
        "location_desc": "Dado sintético para demonstração — não é uma instalação real",
        "gas_type": "CO2",
        "baseline_ppm": 480.0,
        "noise_ppm": 35.0,
    },
    {
        "sensor_id": "demo-sensor-ch4-02",
        "sensor_id_short": 90003,
        "asset_id": "demo-planta-fake-2",
        "name": "[DEMO] Sensor CH4 — Unidade Fictícia Sul",
        "location_desc": "Dado sintético para demonstração — não é uma instalação real",
        "gas_type": "CH4",
        "baseline_ppm": 110.0,
        "noise_ppm": 10.0,
    },
]

SAMPLE_INTERVAL_MINUTES = 15
PERIOD_DAYS = 3


def _cleanup(db) -> None:
    demo_sensor_ids = [s["sensor_id"] for s in SENSORS]
    db.query(Alert).filter(Alert.sensor_id.in_(demo_sensor_ids)).delete(synchronize_session=False)
    db.query(Reading).filter(Reading.sensor_id.in_(demo_sensor_ids)).delete(synchronize_session=False)
    db.query(Sensor).filter(Sensor.sensor_id.in_(demo_sensor_ids)).delete(synchronize_session=False)
    db.commit()


def _seed_sensor_readings(db, spec: dict, now: datetime) -> None:
    db.add(
        Sensor(
            sensor_id=spec["sensor_id"],
            sensor_id_short=spec["sensor_id_short"],
            asset_id=spec["asset_id"],
            name=spec["name"],
            location_desc=spec["location_desc"],
            installed_at=now - timedelta(days=PERIOD_DAYS + 30),
            status="active",
        )
    )
    db.commit()

    start = now - timedelta(days=PERIOD_DAYS)
    total_points = int((PERIOD_DAYS * 24 * 60) / SAMPLE_INTERVAL_MINUTES)

    # Um "episódio" de anomalia/alerta no meio do período, pra o dashboard
    # de demo mostrar os três estados possíveis (normal, anomalia, alerta).
    episode_start_idx = total_points // 2
    episode_len = 4  # ~1h de leituras "fora do padrão"

    alert_started_at = None
    alert_max_ppm = None

    for i in range(total_points):
        t = start + timedelta(minutes=i * SAMPLE_INTERVAL_MINUTES)
        in_episode = episode_start_idx <= i < episode_start_idx + episode_len

        if in_episode:
            # Pico bem acima do normal — dispara tanto a marcação de
            # anomalia quanto o alerta de segurança sintéticos.
            ppm = spec["baseline_ppm"] * 5.5 + random.uniform(-5, 5)
            is_anomaly = True
            if alert_started_at is None:
                alert_started_at = t
            alert_max_ppm = ppm if alert_max_ppm is None else max(alert_max_ppm, ppm)
        else:
            ppm = spec["baseline_ppm"] + random.uniform(-spec["noise_ppm"], spec["noise_ppm"])
            is_anomaly = False

        db.add(
            Reading(
                time=t,
                sensor_id=spec["sensor_id"],
                gas_type=spec["gas_type"],
                concentration_ppm=round(ppm, 1),
                temperature_c=round(24.0 + random.uniform(-1.5, 1.5), 1),
                battery_pct=round(max(60.0, 100.0 - i * 0.05), 1),
                is_anomaly=is_anomaly,
            )
        )

    db.commit()

    if alert_started_at is not None:
        alert_ended_at = alert_started_at + timedelta(minutes=SAMPLE_INTERVAL_MINUTES * episode_len)
        db.add(
            Alert(
                sensor_id=spec["sensor_id"],
                gas_type=spec["gas_type"],
                started_at=alert_started_at,
                ended_at=alert_ended_at,
                max_ppm=round(alert_max_ppm, 1),
                status="resolved",
                notified_at=alert_started_at + timedelta(minutes=2),
            )
        )
        db.commit()


def main() -> None:
    db = SessionLocal()
    random.seed(42)  # dados reprodutíveis entre execuções
    now = datetime.now(timezone.utc)

    try:
        _cleanup(db)
        for spec in SENSORS:
            _seed_sensor_readings(db, spec, now)

        total_readings = (
            db.query(Reading)
            .filter(Reading.sensor_id.in_([s["sensor_id"] for s in SENSORS]))
            .count()
        )
        total_alerts = (
            db.query(Alert)
            .filter(Alert.sensor_id.in_([s["sensor_id"] for s in SENSORS]))
            .count()
        )
        print(
            f"OK: {len(SENSORS)} sensores fictícios, {total_readings} leituras "
            f"sintéticas e {total_alerts} alertas de exemplo seedados"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
