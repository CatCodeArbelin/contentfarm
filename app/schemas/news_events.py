from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import Status


class NewsEventBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    summary: str
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    platform: str | None = None
    strategy: str | None = None
    status: Status = Status.pending
    raw_item_ids: list[int] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0)
    reasons: list[dict[str, Any]] = Field(default_factory=list)


class NewsEventCreate(NewsEventBase):
    pass


class NewsEventRead(NewsEventBase):
    id: int
    created_at: datetime
