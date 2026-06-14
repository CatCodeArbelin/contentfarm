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
MinScoreQuery = Annotated[float | None, Query(ge=0, description="Return records with score greater than or equal to this value.")]
MaxScoreQuery = Annotated[float | None, Query(ge=0, description="Return records with score less than or equal to this value.")]
SortByQuery = Annotated[str, Query(pattern="^(created_at|score)$", description="Field used to sort records.")]
SortOrderQuery = Annotated[str, Query(pattern="^(asc|desc)$", description="Sort direction.")]

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
        score = getattr(item, "score", None)
        if filters.min_score is not None and (score is None or score < filters.min_score):
            return False
        if filters.max_score is not None and (score is None or score > filters.max_score):
            return False
        return True

    filtered = [item for item in items if keep(item)]
    reverse = filters.sort_order == "desc"
    filtered.sort(key=lambda item: getattr(item, filters.sort_by, None) or 0, reverse=reverse)
    return filtered[offset : offset + limit], len(filtered)
