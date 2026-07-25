"""
Script standalone (sem pytest). Requer TimescaleDB rodando e migrations
aplicadas. Sobe a API REST via uvicorn numa thread local (porta efêmera),
bate nela via httpx real (não TestClient simulado), e derruba o servidor ao
final. Tem timeouts explícitos de start/stop — não fica rodando pra sempre.
Roda: python tests/test_api.py
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

TEST_SENSOR_ID = "test-sensor-api"
TEST_SENSOR_ID_SHORT = 65003
TEST_USER_EMAIL = "test-api@methane-co2-tracker.local"
TEST_USER_PASSWORD = "senha-de-teste-123"
HOST = "127.0.0.1"
PORT = 8931
BASE_URL = f"http://{HOST}:{PORT}"
SERVER_START_TIMEOUT = 10
SERVER_STOP_TIMEOUT = 10


def _cleanup(db) -> None:
    db.query(Alert).filter(Alert.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Reading).filter(Reading.sensor_id == TEST_SENSOR_ID).delete()
    db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR_ID).delete()
    db.query(User).filter(User.email == TEST_USER_EMAIL).delete()
    db.commit()


def _seed(db) -> None:
    db.add(User(email=TEST_USER_EMAIL, password_hash=hash_password(TEST_USER_PASSWORD)))
    db.add(
        Sensor(
            sensor_id=TEST_SENSOR_ID,
            sensor_id_short=TEST_SENSOR_ID_SHORT,
            asset_id="test-asset",
            name="Sensor de teste - API",
            installed_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    now = datetime.now(timezone.utc)
    for i in range(5):
        db.add(
            Reading(
                time=now - timedelta(minutes=i),
                sensor_id=TEST_SENSOR_ID,
                gas_type="CH4" if i % 2 == 0 else "CO2",
                concentration_ppm=100 + i,
            )
        )
    db.add(
        Alert(
            sensor_id=TEST_SENSOR_ID,
            gas_type="CH4",
            started_at=now - timedelta(minutes=10),
            ended_at=now - timedelta(minutes=8),
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

    try:
        _cleanup(db)
        _seed(db)

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

        # Sem token -> 401, nenhum endpoint aberto.
        r = httpx.get(f"{BASE_URL}/readings", timeout=5)
        assert r.status_code == 401, f"esperava 401 sem token, recebeu {r.status_code}"

        # Com token inválido -> 401.
        r = httpx.get(f"{BASE_URL}/readings", headers={"Authorization": "Bearer chave-errada"}, timeout=5)
        assert r.status_code == 401

        # /readings: filtro por gas_type + paginação.
        r = httpx.get(
            f"{BASE_URL}/readings",
            params={"device_id": TEST_SENSOR_ID, "gas_type": "CH4", "limit": 2},
            headers=headers_ok,
            timeout=5,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["total"] == 3, f"esperava 3 leituras CH4, recebeu {body['total']}"
        assert len(body["items"]) == 2, "limit=2 deveria truncar os items"
        assert all(item["gas_type"] == "CH4" for item in body["items"])

        # /readings: filtro por período (start no momento da checagem exclui
        # todas as leituras seedadas antes dele).
        cutoff = datetime.now(timezone.utc).isoformat()
        r = httpx.get(
            f"{BASE_URL}/readings",
            params={"device_id": TEST_SENSOR_ID, "start": cutoff},
            headers=headers_ok,
            timeout=5,
        )
        assert r.status_code == 200
        assert r.json()["total"] == 0, "filtro de período deveria zerar o resultado"

        # /devices e /devices/{id}.
        r = httpx.get(f"{BASE_URL}/devices", headers=headers_ok, timeout=5)
        assert r.status_code == 200
        assert any(d["sensor_id"] == TEST_SENSOR_ID for d in r.json()["items"])

        r = httpx.get(f"{BASE_URL}/devices/{TEST_SENSOR_ID}", headers=headers_ok, timeout=5)
        assert r.status_code == 200
        assert r.json()["sensor_id"] == TEST_SENSOR_ID

        r = httpx.get(f"{BASE_URL}/devices/sensor-que-nao-existe", headers=headers_ok, timeout=5)
        assert r.status_code == 404

        # /alerts: filtro por status.
        r = httpx.get(
            f"{BASE_URL}/alerts",
            params={"device_id": TEST_SENSOR_ID, "status": "resolved"},
            headers=headers_ok,
            timeout=5,
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1

        # Nenhum endpoint aberto: docs/openapi desligados.
        r = httpx.get(f"{BASE_URL}/docs", timeout=5)
        assert r.status_code == 404

        print("OK: API REST — auth obrigatória, paginação, filtros por gas/período/status")
    finally:
        server.should_exit = True
        thread.join(timeout=SERVER_STOP_TIMEOUT)
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
