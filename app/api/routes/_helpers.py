from datetime import datetime, timezone
from typing import Annotated, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.schemas.common import ListFilters, Status

LimitQuery = Annotated[int, Query(ge=1, le=200, description="Maximum number of records to return.")]
OffsetQuery = Annotated[int, Query(ge=0, description="Number of records to skip.")]
StatusQuery = Annotated[Status | None, Query(description="Filter by workflow status.")]
TextQuery = Annotated[str | None, Query(description="Optional exact-match filter.")]
CreatedAtQuery = Annotated[datetime | None, Query(description="Return records created at or after this timestamp.")]

T = TypeVar("T", bound=BaseModel)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def apply_filters(items: list[T], filters: ListFilters, limit: int, offset: int) -> tuple[list[T], int]:
    def keep(item: T) -> bool:
        for field in ("status", "language", "topic", "platform", "strategy"):
            expected = getattr(filters, field)
            if expected is not None and getattr(item, field, None) != expected:
                return False
        if filters.created_at is not None and getattr(item, "created_at", filters.created_at) < filters.created_at:
            return False
        return True

    filtered = [item for item in items if keep(item)]
    return filtered[offset : offset + limit], len(filtered)
