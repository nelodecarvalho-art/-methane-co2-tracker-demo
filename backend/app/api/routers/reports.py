from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.reports.compliance_report import build_compliance_pdf

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_user)])


@router.get("/compliance")
def get_compliance_report(
    start: datetime = Query(..., description="Início do período (inclusive)"),
    end: datetime = Query(..., description="Fim do período (inclusive)"),
    db: Session = Depends(get_db),
) -> Response:
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end deve ser posterior a start",
        )

    pdf_bytes = build_compliance_pdf(db, start=start, end=end)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio-compliance.pdf"},
    )
