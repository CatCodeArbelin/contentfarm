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
    prompt_id: int | None = None
    prompt_version: str | None = None


class GenerationRead(BaseModel):
    id: int
    news_event_id: int
    strategy: str
    language: str
    topic: str | None = None
    platform: str | None = None
    status: Status
    output: str | None = None
    prompt_id: int | None = None
    prompt_version: str | None = None
    created_at: datetime


class GeneratedVariantRead(BaseModel):
    id: int
    news_event_id: int
    title: str | None = None
    lead: str | None = None
    body: str | None = None
    sources: list[str] | None = None
    platform: str
    strategy: str
    risk_level: str
    status: Status
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    news_event_id: int


class GenerateResponse(BaseModel):
    generated_variants: list[GeneratedVariantRead]
