from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery
from app.api.routes.db_helpers import commit_or_rollback, enum_dump, get_model_or_404, list_models
from app.db.session import get_db
from app.models.content import Metric
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.metrics import MetricCreate, MetricRead

router = APIRouter(prefix="/metrics", tags=["Metrics"])


def _model_data(payload: MetricCreate, *, exclude_unset: bool = False) -> dict[str, object]:
    data = enum_dump(payload, exclude_unset=exclude_unset)
    return data


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
    db: Session = Depends(get_db),
) -> PaginatedResponse[MetricRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, Metric, filters, limit, offset)
    return PaginatedResponse[MetricRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=MetricRead, summary="Get metric")
def get_metric(item_id: int, db: Session = Depends(get_db)) -> MetricRead:
    return get_model_or_404(db, Metric, item_id, "Metric")


@router.post("", response_model=MetricRead, status_code=status.HTTP_201_CREATED, summary="Create metric")
def create_metric(payload: MetricCreate, db: Session = Depends(get_db)) -> MetricRead:
    item = Metric(**_model_data(payload))
    db.add(item)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=MetricRead, summary="Update metric")
def update_metric(item_id: int, payload: MetricCreate, db: Session = Depends(get_db)) -> MetricRead:
    item = get_model_or_404(db, Metric, item_id, "Metric")
    for key, value in _model_data(payload, exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_rollback(db)
    db.refresh(item)
    return item
