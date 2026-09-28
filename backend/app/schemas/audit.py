"""Response schemas for query audit history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    query_text: str
    answer_text: str | None
    chunk_ids_used: list[int] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditListResponse(BaseModel):
    total: int
    items: list[AuditLogResponse]
