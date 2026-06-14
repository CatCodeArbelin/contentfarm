from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Status


class ModerationDecision(BaseModel):
    variant_id: int
    status: Status = Field(description="Approved, rejected, or pending_review status.")
    reviewer: str = Field(min_length=1)
    comment: str | None = None


class ModerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    variant_id: int
    status: Status
    reviewer: str
    comment: str | None = None
    language: str | None = None
    topic: str | None = None
    platform: str | None = None
    strategy: str | None = None
    created_at: datetime
