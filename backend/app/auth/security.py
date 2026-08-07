from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.db.session import settings

# Hash "dummy" válido, usado quando o e-mail informado no login não existe —
# faz o bcrypt.checkpw() rodar do mesmo jeito, pra não vazar por tempo de
# resposta se um e-mail está cadastrado ou não.
_DUMMY_HASH = bcrypt.hashpw(b"nao-existe-nenhum-usuario-com-este-email", bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    hash_to_check = password_hash.encode("utf-8") if password_hash else _DUMMY_HASH
    return bcrypt.checkpw(password.encode("utf-8"), hash_to_check)


def create_access_token(user_id: int, expire_minutes: int | None = None) -> tuple[str, int]:
    """Retorna (token, expires_in_seconds). `expire_minutes` sobrescreve o
    default (usado pelo login de demo, que expira mais rápido que um login
    normal)."""
    minutes = expire_minutes if expire_minutes is not None else settings.jwt_access_token_expire_minutes
    expire_delta = timedelta(minutes=minutes)
    expires_at = datetime.now(timezone.utc) + expire_delta
    payload = {"sub": str(user_id), "exp": expires_at}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expire_delta.total_seconds())


def decode_access_token(token: str) -> int | None:
    """Retorna o user_id do token, ou None se inválido/expirado/malformado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
