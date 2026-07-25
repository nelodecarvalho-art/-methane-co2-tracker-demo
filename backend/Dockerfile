FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/

# Roda a migração antes de subir a API a cada deploy — mantém o schema em
# dia automaticamente. $PORT é injetado pela plataforma de hospedagem
# (Railway); default 8000 pra rodar local via `docker run` sem setar nada.
CMD alembic upgrade head && uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
