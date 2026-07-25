"""
Script standalone (sem pytest). Requer TimescaleDB + Mailpit rodando
(docker-compose up timescaledb mailpit) e migrations aplicadas. Simula um
episódio de anomalia inserindo histórico normal seguido de leituras fora do
padrão, chama is_anomaly()/is_new_anomaly_onset() e notify_anomaly() como o
mqtt_consumer faria, e confirma: notifica só uma vez no início do episódio
(não repete leitura a leitura), via e-mail (Mailpit) e webhook (receptor
local). Tem timeouts explícitos — não fica rodando pra sempre.
Roda: python tests/test_anomaly_notifications.py
"""
import http.server
import json
import random
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.anomaly.detector import is_anomaly, is_new_anomaly_onset  # noqa: E402
from app.anomaly.notify import notify_anomaly  # noqa: E402
from app.db.session import SessionLocal, settings  # noqa: E402
from app.models.orm import Reading, Sensor  # noqa: E402

TEST_SENSOR_ID = "test-sensor-anomaly-notify"
TEST_SENSOR_ID_SHORT = 65005
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 8933
MAILPIT_URL = f"http://{settings.smtp_host}:8025"
MAIL_POLL_TIMEOUT = 10


def _cleanup(db) -> None:
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.commit()


def _cleanup_mailpit() -> None:
    """Apaga e-mails de execuções anteriores deste teste — sem isso, o
    Mailpit acumula mensagens entre execuções e a contagem exata de e-mails
    (deve ser sempre 1) quebraria a partir da segunda vez que este teste
    rodar."""
    resp = httpx.get(
        f"{MAILPIT_URL}/api/v1/search",
        params={"query": TEST_SENSOR_ID},
        timeout=5,
    )
    if resp.status_code != 200:
        return
    ids = [m["ID"] for m in resp.json().get("messages", [])]
    if ids:
        httpx.request("DELETE", f"{MAILPIT_URL}/api/v1/messages", json={"IDs": ids}, timeout=5)


def _insert_reading(db, t: datetime, ppm: float, temp: float, battery: float) -> Reading:
    reading = Reading(
        time=t,
        sensor_id=TEST_SENSOR_ID,
        gas_type="CH4",
        concentration_ppm=ppm,
        temperature_c=temp,
        battery_pct=battery,
    )
    db.add(reading)
    db.commit()
    return reading


class _WebhookCapture(http.server.BaseHTTPRequestHandler):
    received: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802 (nome exigido pela stdlib)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _WebhookCapture.received.append(json.loads(body))
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args) -> None:
        pass  # silencia o log padrão do BaseHTTPRequestHandler


def main() -> None:
    db = SessionLocal()
    random.seed(7)

    webhook_server = http.server.HTTPServer((WEBHOOK_HOST, WEBHOOK_PORT), _WebhookCapture)
    webhook_thread = threading.Thread(target=webhook_server.serve_forever, daemon=True)
    webhook_thread.start()

    original_webhook_url = settings.anomaly_webhook_url
    settings.anomaly_webhook_url = f"http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/anomalias"

    try:
        _cleanup(db)
        _cleanup_mailpit()
        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=TEST_SENSOR_ID_SHORT,
                asset_id="test-asset",
                name="Sensor de teste - notificação de anomalia",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        t = datetime.now(timezone.utc) - timedelta(hours=2)
        for _ in range(settings.anomaly_min_history + 20):
            t += timedelta(seconds=30)
            _insert_reading(
                db, t,
                ppm=80.0 + random.uniform(-3, 3),
                temp=25.0 + random.uniform(-0.5, 0.5),
                battery=90.0 + random.uniform(-1, 1),
            )

        def process(reading: Reading) -> None:
            reading.is_anomaly = is_anomaly(db, TEST_SENSOR_ID, "CH4", reading.time)
            db.commit()
            if reading.is_anomaly and is_new_anomaly_onset(db, TEST_SENSOR_ID, "CH4", reading.time):
                notify_anomaly(reading)

        # Três leituras seguidas fora do padrão -> só a primeira deve notificar.
        t += timedelta(seconds=30)
        r1 = _insert_reading(db, t, ppm=850.0, temp=60.0, battery=90.0)
        process(r1)
        assert r1.is_anomaly is True, "primeira leitura do pico deveria ser marcada como anomalia"

        t += timedelta(seconds=30)
        r2 = _insert_reading(db, t, ppm=860.0, temp=61.0, battery=90.0)
        process(r2)

        t += timedelta(seconds=30)
        r3 = _insert_reading(db, t, ppm=855.0, temp=60.5, battery=90.0)
        process(r3)

        # --- e-mail: consulta a API HTTP do Mailpit — deve haver exatamente 1 ---
        # Nota: o campo "total" da resposta do Mailpit é o total da caixa
        # inteira, não da busca filtrada — a contagem filtrada correta é
        # "messages_count" (e len(messages)).
        deadline = time.time() + MAIL_POLL_TIMEOUT
        mail_hit = None
        while time.time() < deadline:
            resp = httpx.get(
                f"{MAILPIT_URL}/api/v1/search",
                params={"query": TEST_SENSOR_ID},
                timeout=5,
            )
            if resp.status_code == 200 and resp.json()["messages_count"] >= 1:
                mail_hit = resp.json()
                break
            time.sleep(0.5)
        assert mail_hit is not None, f"e-mail de anomalia não apareceu no Mailpit em {MAIL_POLL_TIMEOUT}s"
        assert mail_hit["messages_count"] == 1, (
            f"esperava exatamente 1 e-mail (só no início do episódio), recebeu {mail_hit['messages_count']}"
        )
        assert "[ANOMALIA]" in mail_hit["messages"][0]["Subject"]

        # --- webhook: aguarda o receptor local, também deve ter exatamente 1 ---
        deadline = time.time() + MAIL_POLL_TIMEOUT
        while len(_WebhookCapture.received) < 1 and time.time() < deadline:
            time.sleep(0.2)
        time.sleep(0.5)  # sobra pra garantir que um segundo POST indevido teria chegado
        assert len(_WebhookCapture.received) == 1, (
            f"esperava exatamente 1 webhook, recebeu {len(_WebhookCapture.received)}"
        )
        payload = _WebhookCapture.received[0]
        assert payload["device_id"] == TEST_SENSOR_ID
        assert payload["type"] == "anomaly"
        assert payload["value_ppm"] == 850.0

        print(
            "OK: notificação de anomalia — dispara só no início do episódio "
            "(e-mail via Mailpit + webhook), não repete leitura a leitura"
        )
    finally:
        settings.anomaly_webhook_url = original_webhook_url
        webhook_server.shutdown()
        webhook_thread.join(timeout=10)
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
