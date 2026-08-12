import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.rate_limit import limiter
from app.db.session import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin_task_secret(request: Request) -> None:
    """Autenticação separada do login de usuário: pensada para uma tarefa
    agendada externa chamar sem precisar de e-mail/senha nem lidar com
    expiração de JWT. Desligado por padrão (404) — uma instalação de
    cliente real não deve ter essa porta aberta sem decisão explícita.
    """
    if not settings.admin_task_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    provided = request.headers.get("X-Admin-Task-Secret", "")
    if not hmac.compare_digest(provided, settings.admin_task_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Admin-Task-Secret ausente ou inválido",
        )


@router.post("/reseed-demo")
@limiter.limit("5/minute")
def reseed_demo(
    request: Request,  # exigido pelo slowapi para extrair o IP do rate limit
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin_task_secret),
) -> dict:
    from scripts.seed_demo_data import reseed

    result = reseed(db)
    logger.info(
        "demo reseedada via /admin/reseed-demo (sensors=%s readings=%s alerts=%s)",
        result["sensors"],
        result["readings"],
        result["alerts"],
    )
    return result
