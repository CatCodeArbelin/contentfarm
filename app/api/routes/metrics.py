from fastapi import APIRouter, status

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, apply_filters, now_utc
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.metrics import MetricCreate, MetricRead

router = APIRouter(prefix="/metrics", tags=["Metrics"])

_ITEMS: list[MetricRead] = []


@router.get("", response_model=PaginatedResponse[MetricRead], summary="List metrics")
def list_metrics(
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
    status: StatusQuery = None,
    language: TextQuery = None,
    topic: TextQuery = None,
    platform: TextQuery = None,
    strategy: TextQuery = None,
    created_at: CreatedAtQuery = None,
) -> PaginatedResponse[MetricRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = apply_filters(_ITEMS, filters, limit, offset)
    return PaginatedResponse[MetricRead](items=items, limit=limit, offset=offset, total=total)


@router.post("", response_model=MetricRead, status_code=status.HTTP_201_CREATED, summary="Create metric")
def create_metric(payload: MetricCreate) -> MetricRead:
    item = MetricRead(id=len(_ITEMS) + 1, created_at=now_utc(), **payload.model_dump())
    _ITEMS.append(item)
    return item
