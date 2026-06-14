from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.news_events import NewsEventCreate, NewsEventRead

router = APIRouter(prefix="/news-events", tags=["NewsEvents"])

_ITEMS: list[NewsEventRead] = []


@router.get("", response_model=PaginatedResponse[NewsEventRead], summary="List news events")
def list_news_events(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[NewsEventRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[NewsEventRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=NewsEventRead, status_code=status.HTTP_201_CREATED, summary="Create newsevent")
def create_newsevent(payload: NewsEventCreate) -> NewsEventRead:
    item = NewsEventRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
