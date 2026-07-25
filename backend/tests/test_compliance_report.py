"""
Script standalone (sem pytest). Requer TimescaleDB rodando e migrations
aplicadas. Sobe a API REST via uvicorn numa thread local (porta efêmera),
bate no endpoint /reports/compliance via httpx real, e derruba o servidor
ao final. Roda: python tests/test_compliance_report.py
"""
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.main import app  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.orm import Alert, Reading, Sensor, User  # noqa: E402

TEST_SENSOR_ID = "test-sensor-compliance-report"
TEST_SENSOR_ID_SHORT = 65004
TEST_USER_EMAIL = "test-compliance-report@methane-co2-tracker.local"
TEST_USER_PASSWORD = "senha-de-teste-123"
HOST = "127.0.0.1"
PORT = 8932
BASE_URL = f"http://{HOST}:{PORT}"
SERVER_START_TIMEOUT = 10
SERVER_STOP_TIMEOUT = 10


def _cleanup(db) -> None:
    db.query(Alert).filter(Alert.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.query(User).filter(User.email == TEST_USER_EMAIL).delete()
    db.commit()


def _seed(db, period_start: datetime) -> None:
    db.add(User(email=TEST_USER_EMAIL, password_hash=hash_password(TEST_USER_PASSWORD)))
    db.add(
        Sensor(
            sensor_id=TEST_SENSOR_ID,
            sensor_id_short=TEST_SENSOR_ID_SHORT,
            asset_id="test-asset",
            name="Sensor de teste - relatório de compliance",
            installed_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    for i in range(5):
        db.add(
            Reading(
                time=period_start + timedelta(minutes=i),
                sensor_id=TEST_SENSOR_ID,
                gas_type="CH4",
                concentration_ppm=100 + i,
                temperature_c=25.0,
                battery_pct=90.0,
                is_anomaly=(i == 4),
            )
        )
    db.add(
        Alert(
            sensor_id=TEST_SENSOR_ID,
            gas_type="CH4",
            started_at=period_start + timedelta(minutes=1),
            ended_at=period_start + timedelta(minutes=3),
            max_ppm=650,
            status="resolved",
        )
    )
    db.commit()


def main() -> None:
    db = SessionLocal()
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    period_start = datetime.now(timezone.utc) - timedelta(days=1)
    period_end = period_start + timedelta(hours=1)

    try:
        _cleanup(db)
        _seed(db, period_start)

        thread.start()
        deadline = time.time() + SERVER_START_TIMEOUT
        while not server.started and time.time() < deadline:
            time.sleep(0.1)
        assert server.started, "servidor uvicorn não subiu a tempo"

        login_resp = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=5,
        )
        assert login_resp.status_code == 200, login_resp.text
        headers_ok = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        # Sem token -> 401.
        r = httpx.get(
            f"{BASE_URL}/reports/compliance",
            params={"start": period_start.isoformat(), "end": period_end.isoformat()},
            timeout=5,
        )
        assert r.status_code == 401

        # end <= start -> 400.
        r = httpx.get(
            f"{BASE_URL}/reports/compliance",
            params={"start": period_end.isoformat(), "end": period_start.isoformat()},
            headers=headers_ok,
            timeout=5,
        )
        assert r.status_code == 400, f"esperava 400 com end<=start, recebeu {r.status_code}"

        # Período com dados -> PDF válido contendo as leituras e o alerta seedados.
        r = httpx.get(
            f"{BASE_URL}/reports/compliance",
            params={"start": period_start.isoformat(), "end": period_end.isoformat()},
            headers=headers_ok,
            timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.headers["content-type"] == "application/pdf"
        assert r.content.startswith(b"%PDF"), "resposta não parece ser um PDF válido"
        assert len(r.content) > 500, "PDF suspeito de estar vazio/truncado"

        # Período sem nenhum dado -> ainda gera um PDF válido (relatório vazio, não erro).
        empty_start = period_end + timedelta(days=30)
        empty_end = empty_start + timedelta(hours=1)
        r = httpx.get(
            f"{BASE_URL}/reports/compliance",
            params={"start": empty_start.isoformat(), "end": empty_end.isoformat()},
            headers=headers_ok,
            timeout=10,
        )
        assert r.status_code == 200
        assert r.content.startswith(b"%PDF")

        print("OK: relatório de compliance — auth obrigatória, validação de período, PDF com e sem dados")
    finally:
        server.should_exit = True
        thread.join(timeout=SERVER_STOP_TIMEOUT)
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
