from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import Status


class RawItemBase(BaseModel):
    source_id: int
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl = Field(
        validation_alias=AliasChoices("url", "source_url"),
        serialization_alias="url",
    )
    content: str
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    platform: str | None = None
    strategy: str | None = None
    status: Status = Status.pending


class RawItemCreate(RawItemBase):
    pass


class RawItemRead(RawItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
