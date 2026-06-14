from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import Status


class VariantBase(BaseModel):
    generation_id: int
    platform: str = Field(examples=["telegram"])
    strategy: str
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    content: str
    status: Status = Status.pending_review


class VariantCreate(VariantBase):
    pass


class VariantRead(VariantBase):
    id: int
    created_at: datetime
