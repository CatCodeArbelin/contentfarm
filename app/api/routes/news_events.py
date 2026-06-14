from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, MaxScoreQuery, MinScoreQuery, OffsetQuery, SortByQuery, SortOrderQuery, StatusQuery, TextQuery
from app.api.routes.db_helpers import commit_or_rollback, enum_dump, get_model_or_404, list_models
from app.db.session import get_db
from app.models.content import NewsEvent, SourceLink
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.news_events import NewsEventCreate, NewsEventRead

router = APIRouter(prefix="/news-events", tags=["NewsEvents"])


def _model_data(payload: NewsEventCreate, *, exclude_unset: bool = False) -> tuple[dict[str, object], list[int]]:
    data = enum_dump(payload, exclude_unset=exclude_unset)
    raw_item_ids = data.pop("raw_item_ids", [])
    return data, raw_item_ids


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
    min_score: MinScoreQuery = None,
    max_score: MaxScoreQuery = None,
    sort_by: SortByQuery = "created_at",
    sort_order: SortOrderQuery = "desc",
    db: Session = Depends(get_db),
) -> PaginatedResponse[NewsEventRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at, min_score=min_score, max_score=max_score, sort_by=sort_by, sort_order=sort_order)
    items, total = list_models(db, NewsEvent, filters, limit, offset)
    return PaginatedResponse[NewsEventRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=NewsEventRead, summary="Get news event")
def get_news_event(item_id: int, db: Session = Depends(get_db)) -> NewsEventRead:
    return get_model_or_404(db, NewsEvent, item_id, "News event")


@router.post("", response_model=NewsEventRead, status_code=status.HTTP_201_CREATED, summary="Create news event")
def create_news_event(payload: NewsEventCreate, db: Session = Depends(get_db)) -> NewsEventRead:
    data, raw_item_ids = _model_data(payload)
    event = NewsEvent(**data)
    db.add(event)
    db.flush()
    for raw_item_id in raw_item_ids:
        db.add(SourceLink(news_event_id=event.id, raw_item_id=raw_item_id, language=event.language, topic=event.topic, platform=event.platform, strategy=event.strategy, score=event.score, risk_level=event.risk_level, reasons=event.reasons))
    commit_or_rollback(db)
    db.refresh(event)
    return event


@router.patch("/{item_id}", response_model=NewsEventRead, summary="Update news event")
def update_news_event(item_id: int, payload: NewsEventCreate, db: Session = Depends(get_db)) -> NewsEventRead:
    event = get_model_or_404(db, NewsEvent, item_id, "News event")
    data, raw_item_ids = _model_data(payload, exclude_unset=True)
    for key, value in data.items():
        setattr(event, key, value)
    if raw_item_ids:
        for raw_item_id in raw_item_ids:
            db.add(SourceLink(news_event_id=event.id, raw_item_id=raw_item_id, language=event.language, topic=event.topic, platform=event.platform, strategy=event.strategy, score=event.score, risk_level=event.risk_level, reasons=event.reasons))
    commit_or_rollback(db)
    db.refresh(event)
    return event
