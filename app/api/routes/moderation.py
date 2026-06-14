from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.moderation import ModerationDecision, ModerationRead

router = APIRouter(prefix="/moderation", tags=["Moderation"])

_ITEMS: list[ModerationRead] = []


@router.get("", response_model=PaginatedResponse[ModerationRead], summary="List moderation decisions")
def list_moderation(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[ModerationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[ModerationRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=ModerationRead, status_code=status.HTTP_201_CREATED, summary="Record moderation decision")
def record_decision(payload: ModerationDecision) -> ModerationRead:
    item = ModerationRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
