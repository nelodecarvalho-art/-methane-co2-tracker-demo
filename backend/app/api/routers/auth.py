import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.rate_limit import limiter
from app.api.schemas import LoginRequest, TokenResponse
from app.auth.security import create_access_token, verify_password
from app.db.session import settings
from app.models.orm import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,  # exigido pelo slowapi para extrair o IP do rate limit
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).one_or_none()

    # verify_password roda o bcrypt mesmo quando `user` é None (hash dummy
    # interno) — não vaza por tempo de resposta se o e-mail existe ou não.
    if not verify_password(payload.password, user.password_hash if user else None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    token, expires_in = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=expires_in, role=user.role)


@router.post("/demo-login", response_model=TokenResponse)
@limiter.limit("5/minute")
def demo_login(
    request: Request,  # exigido pelo slowapi para extrair o IP do rate limit
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Emite um token pra conta de demonstração pública sem pedir nenhuma
    credencial — não há senha nem no frontend nem em trânsito. Só funciona
    se DEMO_ACCOUNT_EMAIL estiver configurado E essa conta tiver
    role="viewer" no banco; qualquer outro caso é 404, como se o endpoint
    não existisse (é o estado esperado numa instalação de cliente real).
    """
    not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if not settings.demo_account_email:
        raise not_found

    user = db.query(User).filter(User.email == settings.demo_account_email).one_or_none()
    if user is None or user.role != "viewer":
        raise not_found

    token, expires_in = create_access_token(user.id, expire_minutes=settings.demo_login_expire_minutes)
    logger.info("demo login emitido (user_id=%s)", user.id)
    return TokenResponse(access_token=token, expires_in=expires_in, role=user.role)
