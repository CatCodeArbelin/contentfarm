from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import Status


class GenerationRequest(BaseModel):
    news_event_id: int
    strategy: str = Field(examples=["telegram_short"])
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    platform: str | None = None
    prompt: str | None = None


class GenerationRead(BaseModel):
    id: int
    news_event_id: int
    strategy: str
    language: str
    topic: str | None = None
    platform: str | None = None
    status: Status
    output: str | None = None
    created_at: datetime
