from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Status


class MetricCreate(BaseModel):
    publication_id: int
    platform: str
    name: str = Field(examples=["views"])
    value: float
    language: str | None = None
    topic: str | None = None
    strategy: str | None = None
    status: Status = Status.active


class MetricRead(MetricCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
