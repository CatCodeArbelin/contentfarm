from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery
from app.api.routes.db_helpers import commit_or_rollback, enum_dump, get_model_or_404, list_models
from app.db.session import get_db
from app.models.content import GeneratedVariant, ModerationAudit
from app.schemas.common import ListFilters, PaginatedResponse
from app.schemas.moderation import ModerationDecision, ModerationRead

router = APIRouter(prefix="/moderation", tags=["Moderation"])


@router.get("", response_model=PaginatedResponse[ModerationRead], summary="List moderation decisions")
def list_moderation(limit: LimitQuery = 50, offset: OffsetQuery = 0, status: StatusQuery = None, language: TextQuery = None, topic: TextQuery = None, platform: TextQuery = None, strategy: TextQuery = None, created_at: CreatedAtQuery = None, db: Session = Depends(get_db)) -> PaginatedResponse[ModerationRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, ModerationAudit, filters, limit, offset)
    return PaginatedResponse[ModerationRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=ModerationRead, summary="Get moderation decision")
def get_moderation(item_id: int, db: Session = Depends(get_db)) -> ModerationRead:
    return get_model_or_404(db, ModerationAudit, item_id, "Moderation decision")


@router.post("", response_model=ModerationRead, status_code=status.HTTP_201_CREATED, summary="Record moderation decision")
def record_moderation(payload: ModerationDecision, db: Session = Depends(get_db)) -> ModerationRead:
    variant = get_model_or_404(db, GeneratedVariant, payload.variant_id, "Variant")
    item = ModerationAudit(**enum_dump(payload), language=variant.language, topic=variant.topic, platform=variant.platform, strategy=variant.strategy)
    variant.status = payload.status.value
    db.add(item)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ModerationRead, summary="Update moderation decision")
def update_moderation(item_id: int, payload: ModerationDecision, db: Session = Depends(get_db)) -> ModerationRead:
    item = get_model_or_404(db, ModerationAudit, item_id, "Moderation decision")
    for key, value in enum_dump(payload, exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_rollback(db)
    db.refresh(item)
    return item
