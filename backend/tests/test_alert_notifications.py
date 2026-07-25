"""
Script standalone (sem pytest). Requer TimescaleDB + Mailpit rodando
(docker-compose up timescaledb mailpit) e migrations aplicadas. Dispara um
alerta real via evaluate_alert() e confirma as duas entregas: e-mail
(consultado via API HTTP do Mailpit) e webhook (recebido por um receptor
HTTP efêmero local, criado só para este teste). Tem timeouts explícitos —
não fica rodando pra sempre.
Roda: python tests/test_alert_notifications.py
"""
import http.server
import json
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.alerts.rules import evaluate_alert  # noqa: E402
from app.db.session import SessionLocal, settings  # noqa: E402
from app.models.orm import Alert, Reading, Sensor  # noqa: E402

TEST_SENSOR_ID = "test-sensor-notify"
TEST_SENSOR_ID_SHORT = 65004
MAILPIT_URL = f"http://{settings.smtp_host}:8025"
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 8932
MAIL_POLL_TIMEOUT = 10


def _cleanup(db) -> None:
    db.query(Alert).filter(Alert.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.commit()


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

    webhook_server = http.server.HTTPServer((WEBHOOK_HOST, WEBHOOK_PORT), _WebhookCapture)
    webhook_thread = threading.Thread(target=webhook_server.serve_forever, daemon=True)
    webhook_thread.start()

    original_webhook_url = settings.alert_webhook_url
    settings.alert_webhook_url = f"http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/alertas"

    try:
        _cleanup(db)
        db.add(
            Sensor(
                sensor_id=TEST_SENSOR_ID,
                sensor_id_short=TEST_SENSOR_ID_SHORT,
                asset_id="test-asset",
                name="Sensor de teste - notificação de alerta",
                installed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

        threshold = settings.alert_thresholds_ppm["CH4"]
        window = settings.alert_window_seconds
        base_time = datetime.now(timezone.utc)

        for i in range(5):
            t = base_time - timedelta(seconds=window) + timedelta(seconds=i * (window / 4))
            db.add(
                Reading(
                    time=t,
                    sensor_id=TEST_SENSOR_ID,
                    gas_type="CH4",
                    concentration_ppm=threshold + 75,
                )
            )
        db.commit()

        evaluate_alert(db, TEST_SENSOR_ID, "CH4", base_time)

        alert = (
            db.query(Alert)
            .filter(Alert.sensor_id == TEST_SENSOR_ID, Alert.status == "active")
            .one_or_none()
        )
        assert alert is not None, "alerta deveria ter aberto"
        assert alert.notified_at is not None, "notified_at deveria ter sido marcado (email OU webhook entregues)"

        # --- e-mail: consulta a API HTTP do Mailpit ---
        deadline = time.time() + MAIL_POLL_TIMEOUT
        mail_hit = None
        while time.time() < deadline:
            resp = httpx.get(
                f"{MAILPIT_URL}/api/v1/search",
                params={"query": TEST_SENSOR_ID},
                timeout=5,
            )
            if resp.status_code == 200 and resp.json()["total"] >= 1:
                mail_hit = resp.json()["messages"][0]
                break
            time.sleep(0.5)
        assert mail_hit is not None, f"e-mail de alerta não apareceu no Mailpit em {MAIL_POLL_TIMEOUT}s"
        assert TEST_SENSOR_ID in mail_hit["Subject"]
        assert mail_hit["To"][0]["Address"] == settings.alert_email_to

        # --- webhook: aguarda o receptor local capturar o POST ---
        deadline = time.time() + MAIL_POLL_TIMEOUT
        while not _WebhookCapture.received and time.time() < deadline:
            time.sleep(0.2)
        assert _WebhookCapture.received, f"webhook não recebido em {MAIL_POLL_TIMEOUT}s"
        payload = _WebhookCapture.received[0]
        assert payload["device_id"] == TEST_SENSOR_ID
        assert payload["gas_type"] == "CH4"
        assert payload["value_ppm"] == threshold + 75

        print(
            "OK: alerta disparado notificou por e-mail (Mailpit) e webhook "
            "(receptor local), notified_at marcado"
        )
    finally:
        settings.alert_webhook_url = original_webhook_url
        webhook_server.shutdown()
        webhook_thread.join(timeout=10)
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
