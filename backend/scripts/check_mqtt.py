"""
Valida a conexão com o broker MQTT de produção (HiveMQ Cloud: TLS na 8883 +
autenticação) antes do deploy: conecta, se inscreve num tópico isolado e
descartável (_healthcheck/<uuid>, fora do padrão sensors/+/readings — nunca
toca dado real), publica uma mensagem de teste e confirma que ela volta
intacta. Só lê credenciais de os.environ (via app.db.session.settings, que
por sua vez lê o .env carregado abaixo) — nada hardcoded. Deadline total de
30s para o script inteiro, não por etapa.

Roda: python backend/scripts/check_mqtt.py
"""
import sys
import threading
import time
import uuid
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import settings  # noqa: E402

TIMEOUT_SECONDS = 30


def _remaining(deadline: float) -> float:
    return max(0.0, deadline - time.time())


def main() -> None:
    if not settings.mqtt_username or not settings.mqtt_password:
        print("FAIL: MQTT_USERNAME/MQTT_PASSWORD não configurados no ambiente")
        sys.exit(1)
    if not settings.mqtt_use_tls:
        print("FAIL: MQTT_USE_TLS não está ativado — HiveMQ Cloud exige TLS na 8883")
        sys.exit(1)

    deadline = time.time() + TIMEOUT_SECONDS
    topic = f"_healthcheck/{uuid.uuid4()}"
    expected_payload = uuid.uuid4().bytes

    connected = threading.Event()
    subscribed = threading.Event()
    received = threading.Event()
    state: dict = {}

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="methane-co2-tracker-mqtt-check",
    )
    client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    client.tls_set()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            connected.set()
            client.subscribe(topic, qos=1)
        else:
            state["connect_error"] = reason_code

    def on_subscribe(client, userdata, mid, reason_codes, properties=None):
        subscribed.set()

    def on_message(client, userdata, message):
        state["topic"] = message.topic
        state["payload"] = message.payload
        received.set()

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    try:
        client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: connect() levantou {exc.__class__.__name__}: {exc}")
        sys.exit(1)

    client.loop_start()
    try:
        if not connected.wait(timeout=_remaining(deadline)):
            print(
                f"FAIL: não conectou em {TIMEOUT_SECONDS}s "
                f"(host={settings.mqtt_broker_host}:{settings.mqtt_broker_port})"
            )
            sys.exit(1)
        if "connect_error" in state:
            print(f"FAIL: broker recusou a conexão (reason_code={state['connect_error']})")
            sys.exit(1)

        if not subscribed.wait(timeout=_remaining(deadline)):
            print("FAIL: subscribe não confirmado (SUBACK) dentro do prazo")
            sys.exit(1)

        client.publish(topic, expected_payload, qos=1)

        if not received.wait(timeout=_remaining(deadline)):
            print(f"FAIL: mensagem publicada não retornou dentro do prazo (tópico={topic})")
            sys.exit(1)

        assert state["topic"] == topic, "tópico recebido não bate com o publicado"
        assert state["payload"] == expected_payload, "payload recebido não bate com o publicado"

        print(
            f"PASS: TLS conectado a {settings.mqtt_broker_host}:{settings.mqtt_broker_port}, "
            f"publish/subscribe round-trip confirmado em '{topic}'"
        )
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
