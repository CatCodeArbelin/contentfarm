from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery
from app.api.routes.db_helpers import commit_or_rollback, enum_dump, get_model_or_404, list_models
from app.collectors.utils import url_hash
from app.db.session import get_db
from app.models.content import RawItem
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.raw_items import RawItemCreate, RawItemRead

router = APIRouter(prefix="/raw-items", tags=["RawItems"])


def _model_data(payload: RawItemCreate, *, exclude_unset: bool = False) -> dict[str, object]:
    data = enum_dump(payload, exclude_unset=exclude_unset)
    if "url" in data:
        source_url = str(data.pop("url"))
        data["source_url"] = source_url
        data["url_hash"] = url_hash(source_url)
    return data


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
    db: Session = Depends(get_db),
) -> PaginatedResponse[RawItemRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, RawItem, filters, limit, offset)
    return PaginatedResponse[RawItemRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=RawItemRead, summary="Get rawitem")
def get_rawitem(item_id: int, db: Session = Depends(get_db)) -> RawItemRead:
    return get_model_or_404(db, RawItem, item_id, "Rawitem")


@router.post("", response_model=RawItemRead, status_code=status.HTTP_201_CREATED, summary="Create rawitem")
def create_rawitem(payload: RawItemCreate, db: Session = Depends(get_db)) -> RawItemRead:
    item = RawItem(**_model_data(payload))
    db.add(item)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=RawItemRead, summary="Update rawitem")
def update_rawitem(item_id: int, payload: RawItemCreate, db: Session = Depends(get_db)) -> RawItemRead:
    item = get_model_or_404(db, RawItem, item_id, "Rawitem")
    for key, value in _model_data(payload, exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_rollback(db)
    db.refresh(item)
    return item
