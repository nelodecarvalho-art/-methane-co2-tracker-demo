"""
Publica leituras de CH4 = 600 ppm (acima do ALERT_THRESHOLD_PPM_CH4 = 500)
no broker MQTT de produção (HiveMQ Cloud), sustentadas por
ALERT_WINDOW_SECONDS + margem, no mesmo formato Protobuf e tópico
(sensors/<sensor_id_short>/readings) que o consumer real espera. Objetivo:
validar o pipeline ponta a ponta (MQTT -> decode -> TimescaleDB -> regra
de alerta -> notificação) sem sensor físico.

NÃO limpa os dados no final de propósito — a ideia é você conferir no
dashboard/API/e-mail depois que o script terminar. O sensor sintético
fica claramente identificado (sensor_id="smoke-test-ch4",
name="[SMOKE TEST] ...") pra não ser confundido com dado real.

Pré-requisito: o worker methane-co2-tracker-mqtt-consumer precisa estar
rodando no Render, configurado com os mesmos DB_*/MQTT_* deste .env local
— senão a mensagem cai no broker e ninguém do lado do backend está
inscrito nela.

Roda: python backend/scripts/smoke_publish_ch4.py
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal, settings  # noqa: E402
from app.ingestion.generated import sensor_reading_pb2 as pb  # noqa: E402
from app.models.orm import Sensor  # noqa: E402

SENSOR_ID = "smoke-test-ch4"
CONCENTRATION_PPM = 600
INTERVAL_SECONDS = 5
MARGIN_SECONDS = 30  # publica além da janela de alerta, pra garantir cobertura completa
FALLBACK_SENSOR_ID_SHORT = 900000  # só usado se a tabela sensors estiver vazia


def _ensure_sensor(db) -> int:
    sensor = db.query(Sensor).filter(Sensor.sensor_id == SENSOR_ID).one_or_none()
    if sensor is not None:
        return sensor.sensor_id_short

    max_short = db.query(Sensor.sensor_id_short).order_by(Sensor.sensor_id_short.desc()).first()
    sensor_id_short = (max_short[0] + 1) if max_short else FALLBACK_SENSOR_ID_SHORT

    sensor = Sensor(
        sensor_id=SENSOR_ID,
        sensor_id_short=sensor_id_short,
        asset_id="smoke-test",
        name="[SMOKE TEST] sensor sintético — validação ponta a ponta",
        location_desc="Não é um sensor físico. Criado por smoke_publish_ch4.py.",
        installed_at=datetime.now(timezone.utc),
    )
    db.add(sensor)
    db.commit()
    return sensor_id_short


def main() -> None:
    if not settings.mqtt_username or not settings.mqtt_use_tls:
        print("FAIL: MQTT_USERNAME/MQTT_USE_TLS não configurados — aponte o .env pro HiveMQ Cloud")
        sys.exit(1)

    db = SessionLocal()
    try:
        sensor_id_short = _ensure_sensor(db)
    finally:
        db.close()

    topic = f"sensors/{sensor_id_short}/readings"
    total_seconds = settings.alert_window_seconds + MARGIN_SECONDS
    n_messages = total_seconds // INTERVAL_SECONDS + 1

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="methane-co2-tracker-smoke-test",
    )
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    if settings.mqtt_use_tls:
        client.tls_set()

    client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
    client.loop_start()

    print(
        f"sensor_id={SENSOR_ID} (sensor_id_short={sensor_id_short}), tópico={topic}\n"
        f"Publicando {n_messages} leituras de CH4={CONCENTRATION_PPM}ppm a cada "
        f"{INTERVAL_SECONDS}s por ~{total_seconds}s "
        f"(janela de alerta={settings.alert_window_seconds}s + {MARGIN_SECONDS}s de margem)...\n"
    )

    for i in range(n_messages):
        now = int(time.time())
        msg = pb.SensorReading(
            sensor_id=sensor_id_short,
            timestamp=now,
            gas_type=pb.CH4,
            concentration_ppm=CONCENTRATION_PPM,
            temperature_c_x10=250,
            battery_pct=90,
        )
        client.publish(topic, msg.SerializeToString(), qos=1)
        print(f"  [{i + 1}/{n_messages}] publicado em t={now}")
        if i < n_messages - 1:
            time.sleep(INTERVAL_SECONDS)

    client.loop_stop()
    client.disconnect()

    print(f"\nOK: publicação concluída (sensor_id={SENSOR_ID}). Veja as instruções de conferência.")


if __name__ == "__main__":
    main()
