from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field


class PublicationVariantStatus(str, Enum):
    draft = "draft"
    needs_review = "needs_review"
    approved = "approved"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class Status(str, Enum):
    draft = "draft"
    needs_review = "needs_review"
    pending = "pending"
    active = "active"
    processing = "processing"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"
    archived = "archived"


class ListFilters(BaseModel):
    status: Status | None = Field(default=None, description="Filter by workflow status.")
    language: str | None = Field(default=None, min_length=2, max_length=16, description="Filter by BCP-47 language code.")
    topic: str | None = Field(default=None, description="Filter by editorial topic.")
    platform: str | None = Field(default=None, description="Filter by source or publishing platform.")
    strategy: str | None = Field(default=None, description="Filter by generation or publication strategy.")
    created_at: datetime | None = Field(default=None, description="Return records created at or after this timestamp.")
    min_score: float | None = Field(default=None, ge=0, description="Return records with score greater than or equal to this value.")
    max_score: float | None = Field(default=None, ge=0, description="Return records with score less than or equal to this value.")
    sort_by: Literal["created_at", "score"] = Field(default="created_at", description="Field used to sort records.")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort direction.")


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of records to return.")
    offset: int = Field(default=0, ge=0, description="Number of records to skip.")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
