from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class Status(str, Enum):
    draft = "draft"
    pending = "pending"
    active = "active"
    processing = "processing"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
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


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of records to return.")
    offset: int = Field(default=0, ge=0, description="Number of records to skip.")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
