import logging

import paho.mqtt.client as mqtt
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.alerts.rules import evaluate_alert
from app.anomaly.detector import is_anomaly, is_new_anomaly_onset
from app.anomaly.notify import notify_anomaly
from app.db.session import SessionLocal, settings
from app.ingestion.decoder import DecodeFailure, decode_reading
from app.ingestion.schemas import ReadingIn
from app.models.orm import Reading

logger = logging.getLogger(__name__)


def _handle_message(raw_payload: bytes) -> None:
    """Pipeline completo pra uma mensagem: decode -> validate -> insert ->
    avalia alerta. Qualquer falha aqui é logada e engolida — uma mensagem
    malformada não pode derrubar o consumer inteiro.
    """
    db = SessionLocal()
    try:
        try:
            decoded = decode_reading(db, raw_payload)
            reading_in = ReadingIn.model_validate(decoded)
        except (DecodeFailure, ValidationError) as exc:
            logger.warning("mensagem MQTT descartada: %s", exc)
            return

        reading = Reading(**reading_in.model_dump())
        db.add(reading)
        try:
            db.commit()
        except IntegrityError:
            # (time, sensor_id) já existe — reentrega esperada do QoS1 numa
            # reconexão MQTT (sessão persistente), não é um erro real.
            db.rollback()
            logger.debug(
                "leitura duplicada descartada (reentrega QoS1): sensor=%s time=%s",
                reading_in.sensor_id,
                reading_in.time,
            )
            return

        evaluate_alert(
            db,
            sensor_id=reading_in.sensor_id,
            gas_type=reading_in.gas_type,
            reading_time=reading_in.time,
        )

        reading.is_anomaly = is_anomaly(
            db,
            sensor_id=reading_in.sensor_id,
            gas_type=reading_in.gas_type,
            reading_time=reading_in.time,
        )
        db.commit()

        if reading.is_anomaly and is_new_anomaly_onset(
            db,
            sensor_id=reading_in.sensor_id,
            gas_type=reading_in.gas_type,
            reading_time=reading_in.time,
        ):
            notify_anomaly(reading)
    except Exception:
        db.rollback()
        logger.exception("falha inesperada processando leitura MQTT")
    finally:
        db.close()


def _on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None) -> None:
    if reason_code == 0:
        logger.info("conectado ao broker MQTT, assinando %s", settings.mqtt_topic_pattern)
        # QoS 1: o broker guarda mensagens não entregues enquanto este
        # client (sessão persistente, ver build_client) fica desconectado
        # — ex. durante hibernação do serviço no Render — e entrega tudo
        # ao reconectar, em vez de perder a leitura.
        client.subscribe(settings.mqtt_topic_pattern, qos=1)
    else:
        logger.error("falha ao conectar no broker MQTT: %s", reason_code)


def _on_disconnect(client: mqtt.Client, userdata, flags, reason_code, properties=None) -> None:
    logger.warning("desconectado do broker MQTT (reason_code=%s), paho vai reconectar", reason_code)


def _on_message(client: mqtt.Client, userdata, message: mqtt.MQTTMessage) -> None:
    _handle_message(message.payload)


def build_client() -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="methane-co2-tracker-consumer",
        # clean_session=False: mantém a sessão (e a fila de mensagens QoS>=1
        # não entregues) no broker entre desconexões, desde que reconecte
        # com este mesmo client_id fixo — é o que sustenta a garantia de
        # não perder leitura durante hibernação do serviço.
        clean_session=False,
    )
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    if settings.mqtt_use_tls:
        client.tls_set()
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_message = _on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    return client


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    client = build_client()
    client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
    client.loop_forever()


if __name__ == "__main__":
    run()
