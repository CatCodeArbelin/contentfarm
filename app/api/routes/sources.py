from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.sources import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["Sources"])

_ITEMS: list[SourceRead] = []


@router.get("", response_model=PaginatedResponse[SourceRead], summary="List sources")
def list_sources(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[SourceRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[SourceRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED, summary="Create source")
def create_source(payload: SourceCreate) -> SourceRead:
    item = SourceRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
