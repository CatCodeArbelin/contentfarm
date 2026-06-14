from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import Status


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: HttpUrl = Field(
        validation_alias=AliasChoices("url", "source_url"),
        serialization_alias="url",
    )
    platform: str = Field(examples=["rss"])
    language: str = Field(default="en", min_length=2, max_length=16)
    topic: str | None = None
    strategy: str | None = None
    status: Status = Status.active


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: HttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("url", "source_url"),
        serialization_alias="url",
    )
    platform: str | None = None
    language: str | None = Field(default=None, min_length=2, max_length=16)
    topic: str | None = None
    strategy: str | None = None
    status: Status | None = None


class SourceRead(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime | None = None
