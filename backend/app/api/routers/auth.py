from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.rate_limit import limiter
from app.api.schemas import LoginRequest, TokenResponse
from app.auth.security import create_access_token, verify_password
from app.models.orm import User

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
