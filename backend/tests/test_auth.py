"""
Script standalone (sem pytest). Requer TimescaleDB rodando e migrations
aplicadas (inclui 0003_add_users_table). Sobe a API REST via uvicorn numa
thread local (porta efêmera), bate nela via httpx real. Tem timeouts
explícitos de start/stop — não fica rodando pra sempre.
Roda: python tests/test_auth.py
"""
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt
import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.main import app  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.db.session import SessionLocal, settings  # noqa: E402
from app.models.orm import User  # noqa: E402

TEST_EMAIL = "test-auth@methane-co2-tracker.local"
TEST_PASSWORD = "senha-de-teste-123"
HOST = "127.0.0.1"
PORT = 8934
BASE_URL = f"http://{HOST}:{PORT}"
SERVER_START_TIMEOUT = 10
SERVER_STOP_TIMEOUT = 10


def _cleanup(db) -> None:
    db.query(User).filter(User.email == TEST_EMAIL).delete()
    db.commit()


def _seed(db) -> int:
    user = User(email=TEST_EMAIL, password_hash=hash_password(TEST_PASSWORD))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def _expired_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def main() -> None:
    db = SessionLocal()
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    try:
        _cleanup(db)
        user_id = _seed(db)

        thread.start()
        deadline = time.time() + SERVER_START_TIMEOUT
        while not server.started and time.time() < deadline:
            time.sleep(0.1)
        assert server.started, "servidor uvicorn não subiu a tempo"

        # Login com credenciais corretas -> 200 + token.
        r = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=5,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0
        valid_token = body["access_token"]

        # Login com senha errada -> 401.
        r = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": "senha-errada"},
            timeout=5,
        )
        assert r.status_code == 401, f"esperava 401 com senha errada, recebeu {r.status_code}"

        # Login com e-mail inexistente -> 401 (não 404 — não vaza se o e-mail existe).
        r = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"email": "nao-existe@methane-co2-tracker.local", "password": "qualquer"},
            timeout=5,
        )
        assert r.status_code == 401, f"esperava 401 com e-mail inexistente, recebeu {r.status_code}"

        # Endpoint protegido sem token -> 401.
        r = httpx.get(f"{BASE_URL}/readings", timeout=5)
        assert r.status_code == 401, f"esperava 401 sem token, recebeu {r.status_code}"

        # Endpoint protegido com token malformado -> 401.
        r = httpx.get(
            f"{BASE_URL}/readings",
            headers={"Authorization": "Bearer isto-nao-e-um-jwt"},
            timeout=5,
        )
        assert r.status_code == 401, f"esperava 401 com token malformado, recebeu {r.status_code}"

        # Endpoint protegido com token expirado -> 401.
        r = httpx.get(
            f"{BASE_URL}/readings",
            headers={"Authorization": f"Bearer {_expired_token(user_id)}"},
            timeout=5,
        )
        assert r.status_code == 401, f"esperava 401 com token expirado, recebeu {r.status_code}"

        # Endpoint protegido com token válido -> 200.
        r = httpx.get(
            f"{BASE_URL}/readings",
            headers={"Authorization": f"Bearer {valid_token}"},
            timeout=5,
        )
        assert r.status_code == 200, r.text

        print(
            "OK: autenticação JWT — login válido/inválido, endpoint protegido "
            "sem token / token malformado / token expirado (401), com token válido (200)"
        )
    finally:
        server.should_exit = True
        thread.join(timeout=SERVER_STOP_TIMEOUT)
        _cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
