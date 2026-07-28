import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.rate_limit import limiter
from app.api.routers import alerts, auth, devices, health, readings, reports
from app.db.session import settings
from app.ingestion.mqtt_consumer import run as run_mqtt_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Thread daemon separada: client.connect() é bloqueante, e não pode
    # atrasar o Uvicorn abrindo a porta (senão o healthcheck do Render mata
    # o processo antes dele ficar pronto). daemon=True some junto quando o
    # processo principal morre, sem precisar de shutdown explícito.
    threading.Thread(target=run_mqtt_consumer, daemon=True).start()
    yield


app = FastAPI(
    title="Methane & CO2 Tracker API",
    lifespan=lifespan,
    # Nenhum endpoint aberto (exceto /auth/login, que é o próprio ponto de
    # entrada): docs/redoc/openapi.json não exigiriam autenticação por
    # padrão, então ficam desligados nesta fase.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Rate limiting por IP — importante em qualquer ambiente exposto
# publicamente (ex: demo pública). Limite geral (definido em
# app/api/rate_limit.py) aplicado automaticamente a todas as rotas via
# SlowAPIMiddleware; /auth/login tem limite adicional mais rígido (ver
# app/api/routers/auth.py) por ser o alvo natural de tentativas de força
# bruta.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(readings.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(reports.router)
