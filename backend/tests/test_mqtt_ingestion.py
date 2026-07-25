"""
Script standalone (sem pytest). Requer TimescaleDB + Mosquitto rodando
(docker-compose up timescaledb mosquitto) e migrations aplicadas. Publica
leituras Protobuf reais no broker local e valida que o consumer decodifica,
valida e grava no TimescaleDB. Tem timeout limitado — não fica rodando pra
sempre. Roda: python tests/test_mqtt_ingestion.py
"""
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal, settings  # noqa: E402
from app.ingestion.generated import sensor_reading_pb2 as pb  # noqa: E402
from app.ingestion.mqtt_consumer import build_client  # noqa: E402
from app.models.orm import Reading, Sensor  # noqa: E402

TEST_SENSOR_ID = "test-sensor-mqtt-ingestion"
TEST_SENSOR_ID_SHORT = 65002
N_MESSAGES = 5
TIMEOUT_SECONDS = 15


def _cleanup(db) -> None:
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.commit()


def _publish_messages() -> None:
    publisher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    publisher.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
    publisher.loop_start()

    topic = f"sensors/{TEST_SENSOR_ID_SHORT}/readings"
    now = int(time.time())
    for i in range(N_MESSAGES):
        msg = pb.SensorReading(
            sensor_id=TEST_SENSOR_ID_SHORT,
            timestamp=now - (N_MESSAGES - i),
            gas_type=pb.CH4,
            concentration_ppm=300 + i,
            temperature_c_x10=250,
            battery_pct=90,
        )
        publisher.publish(topic, msg.SerializeToString(), qos=1)

    # também publica uma mensagem malformada, pra provar que não derruba o consumer
    publisher.publish(topic, b"\xff\xff\xff-isso-nao-e-protobuf-valido", qos=1)

    time.sleep(1)
    publisher.loop_stop()
    publisher.disconnect()


def main() -> None:
    db = SessionLocal()
    try:
        _cleanup(db)
        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=TEST_SENSOR_ID_SHORT,
                asset_id="test-asset",
                name="Sensor de teste - ingestão MQTT",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        consumer = build_client()
        subscribed = threading.Event()
        consumer.on_subscribe = lambda *args, **kwargs: subscribed.set()
        consumer.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
        consumer.loop_start()

        # Espera a confirmação do SUBSCRIBE antes de publicar — sem isso, o
        # broker pode receber as mensagens do publisher antes da inscrição do
        # consumer estar ativa, e elas se perdem (sem sessão persistente).
        if not subscribed.wait(timeout=5):
            raise RuntimeError("consumer não confirmou subscribe em 5s")

        _publish_messages()

        deadline = time.time() + TIMEOUT_SECONDS
        count = 0
        while time.time() < deadline:
            count = (
                db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).count()
            )
            if count >= N_MESSAGES:
                break
            time.sleep(0.5)

        consumer.loop_stop()
        consumer.disconnect()

        assert count == N_MESSAGES, (
            f"esperava {N_MESSAGES} leituras gravadas, encontrei {count} "
            f"(timeout de {TIMEOUT_SECONDS}s) — verifique se mosquitto está rodando"
        )
        print(
            f"OK: {count} leituras publicadas via MQTT/Protobuf decodificadas e "
            "gravadas; mensagem malformada foi descartada sem derrubar o consumer"
        )
    finally:
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
