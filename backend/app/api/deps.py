from collections.abc import Generator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.db.session import SessionLocal
from app.models.orm import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ausente, inválido ou expirado",
    )

    if credentials is None:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise unauthorized

    return user


def require_admin(user: User = Depends(require_user)) -> User:
    """Gate para rotas de escrita/administrativas. Hoje nenhuma rota usa
    isso ainda (a API inteira é somente leitura) — existe como guarda
    pronta pra qualquer endpoint de mutação futuro (criar/editar sensor,
    mudar threshold etc.) já nascer restrito a admin, sem depender de
    alguém lembrar de adicionar o gate na hora.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores",
        )
    return user
