from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import Status


class PublicationRequest(BaseModel):
    variant_id: int
    platform: str = Field(examples=["telegram"])
    strategy: str = Field(examples=["immediate"])
    scheduled_at: datetime | None = None


class ApprovalRequest(BaseModel):
    target_type: str = Field(pattern="^(variant|publication)$")
    target_id: int
    approved_by: str = Field(min_length=1, max_length=200)


class PublishRequest(BaseModel):
    target_type: str = Field(pattern="^(variant|publication)$")
    target_id: int
    platform: str | None = Field(default=None, examples=["telegram", "dzen", "vc.ru", "habr", "dtf", "pikabu", "max"])
    export_format: str | None = Field(default=None, pattern="^(markdown|html)$")
    publication_url: HttpUrl | None = None


class PublicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    variant_id: int
    platform: str
    strategy: str
    language: str | None = None
    topic: str | None = None
    status: Status
    url: HttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("url", "publication_url"),
        serialization_alias="url",
    )
    message_id: str | None = None
    export_path: str | None = None
    error: str | None = None
    created_at: datetime
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
