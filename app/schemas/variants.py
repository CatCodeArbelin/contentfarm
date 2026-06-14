from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Status


class VariantBase(BaseModel):
    generation_id: int
    prompt_id: int | None = None
    prompt_version: str | None = None
    platform: str = Field(examples=["telegram"])
    strategy: str
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    content: str
    title: str | None = None
    lead: str | None = None
    body: str | None = None
    sources: list[str] | None = None
    risk_level: str | None = None
    score: float | None = None
    status: Status = Status.draft


class VariantCreate(VariantBase):
    pass


class VariantRead(VariantBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
