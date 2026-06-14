from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.generation import GenerationRead, GenerationRequest

router = APIRouter(prefix="/generation", tags=["Generation"])

_ITEMS: list[GenerationRead] = []


@router.get("", response_model=PaginatedResponse[GenerationRead], summary="List generation jobs")
def list_generation(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[GenerationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[GenerationRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=GenerationRead, status_code=status.HTTP_202_ACCEPTED, summary="Start generation")
def start_generation(payload: GenerationRequest) -> GenerationRead:
    item = GenerationRead(
        id=len(_ITEMS) + 1,
        news_event_id=payload.news_event_id,
        strategy=payload.strategy,
        language=payload.language,
        topic=payload.topic,
        platform=payload.platform,
        status=Status.processing,
        output=None,
        created_at=now_utc(),
    )
    _ITEMS.append(item)
    return item
