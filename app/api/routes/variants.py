from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.variants import VariantCreate, VariantRead

router = APIRouter(prefix="/variants", tags=["Variants"])

_ITEMS: list[VariantRead] = []


@router.get("", response_model=PaginatedResponse[VariantRead], summary="List variants")
def list_variants(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[VariantRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[VariantRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=VariantRead, status_code=status.HTTP_201_CREATED, summary="Create variant")
def create_variant(payload: VariantCreate) -> VariantRead:
    item = VariantRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
