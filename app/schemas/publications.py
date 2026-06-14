from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import Status


class PublicationRequest(BaseModel):
    variant_id: int
    platform: str = Field(examples=["telegram"])
    strategy: str = Field(examples=["immediate"])
    scheduled_at: datetime | None = None


class PublicationRead(BaseModel):
    id: int
    variant_id: int
    platform: str
    strategy: str
    language: str | None = None
    topic: str | None = None
    status: Status
    url: HttpUrl | None = None
    created_at: datetime
    published_at: datetime | None = None
