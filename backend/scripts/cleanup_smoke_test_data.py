"""
Remove os dados sintéticos do sensor smoke-test-ch4 (alertas, leituras e o
próprio sensor) — gerados só pelos testes de ponta a ponta do pipeline
MQTT -> decode -> banco -> alerta -> notificação (smoke_publish_ch4.py).

Escopo travado por sensor_id literal exato (sem LIKE, sem prefixo) — não
tem como isso alcançar demo-sensor-ch4-01/02, demo-sensor-co2-01 (usados
por seed_demo_data.py) ou qualquer sensor real, mesmo por engano.

Pede confirmação interativa antes de apagar qualquer coisa.

Roda: python backend/scripts/cleanup_smoke_test_data.py
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.orm import Alert, Reading, Sensor  # noqa: E402

SENSOR_ID = "smoke-test-ch4"


def main() -> None:
    db = SessionLocal()
    try:
        n_alerts = db.query(Alert).filter(Alert.sensor_id == SENSOR_ID).count()
        n_readings = db.query(Reading).filter(Reading.sensor_id == SENSOR_ID).count()
        sensor = db.query(Sensor).filter(Sensor.sensor_id == SENSOR_ID).one_or_none()

        print(f"sensor_id alvo: {SENSOR_ID!r}")
        print(f"Vai remover: {n_alerts} alerta(s), {n_readings} leitura(s), "
              f"{1 if sensor else 0} sensor")

        if not sensor and n_alerts == 0 and n_readings == 0:
            print("Nada para remover.")
            return

        confirm = input("Confirma a remoção? Digite 'sim' para prosseguir: ")
        if confirm.strip().lower() != "sim":
            print("Cancelado, nada foi removido.")
            return

        deleted_alerts = (
            db.query(Alert).filter(Alert.sensor_id == SENSOR_ID).delete(synchronize_session=False)
        )
        deleted_readings = (
            db.query(Reading).filter(Reading.sensor_id == SENSOR_ID).delete(synchronize_session=False)
        )
        deleted_sensor = (
            db.query(Sensor).filter(Sensor.sensor_id == SENSOR_ID).delete(synchronize_session=False)
        )
        db.commit()

        print(
            f"OK: removidos {deleted_alerts} alerta(s), {deleted_readings} leitura(s), "
            f"{deleted_sensor} sensor"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
