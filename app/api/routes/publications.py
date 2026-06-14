from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.publications import PublicationRead, PublicationRequest

router = APIRouter(prefix="/publications", tags=["Publications"])

_ITEMS: list[PublicationRead] = []


@router.get("", response_model=PaginatedResponse[PublicationRead], summary="List publications")
def list_publications(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[PublicationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[PublicationRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=PublicationRead, status_code=status.HTTP_202_ACCEPTED, summary="Queue publication")
def queue_publication(payload: PublicationRequest) -> PublicationRead:
    item = PublicationRead(
        id=len(_ITEMS) + 1,
        variant_id=payload.variant_id,
        platform=payload.platform,
        strategy=payload.strategy,
        language=None,
        topic=None,
        status=Status.pending,
        url=None,
        created_at=now_utc(),
        published_at=None,
    )
    _ITEMS.append(item)
    return item
