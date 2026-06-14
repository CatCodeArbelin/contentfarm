from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.raw_items import RawItemCreate, RawItemRead

router = APIRouter(prefix="/raw-items", tags=["RawItems"])

_ITEMS: list[RawItemRead] = []


@router.get("", response_model=PaginatedResponse[RawItemRead], summary="List raw items")
def list_raw_items(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[RawItemRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[RawItemRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=RawItemRead, status_code=status.HTTP_201_CREATED, summary="Create rawitem")
def create_rawitem(payload: RawItemCreate) -> RawItemRead:
    item = RawItemRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
