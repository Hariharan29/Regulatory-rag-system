"""Paginated query audit history endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditListResponse, AuditLogResponse

router = APIRouter()


@router.get("/audit", response_model=AuditListResponse)
def list_audit_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    """Return recent query and answer records, newest first."""
    try:
        total = db.scalar(select(func.count(AuditLog.id))) or 0
        statement = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
        )
        logs = db.scalars(statement).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Audit storage is unavailable.",
        ) from exc

    return AuditListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(log) for log in logs],
    )
