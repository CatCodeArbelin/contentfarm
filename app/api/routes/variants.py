from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._helpers import CreatedAtQuery, LimitQuery, OffsetQuery, StatusQuery, TextQuery, now_utc
from app.api.routes.db_helpers import commit_or_rollback, enum_dump, get_model_or_404, list_models
from app.db.session import get_db
from app.models.content import GeneratedVariant, ModerationAudit
from app.schemas.common import ListFilters, PaginatedResponse, Status
from app.schemas.variants import VariantCreate, VariantRead

router = APIRouter(prefix="/variants", tags=["Variants"])


def _model_data(payload: VariantCreate, *, exclude_unset: bool = False) -> dict[str, object]:
    data = enum_dump(payload, exclude_unset=exclude_unset)
    if "generation_id" in data:
        data["news_event_id"] = data.pop("generation_id")
    return data


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
    db: Session = Depends(get_db),
) -> PaginatedResponse[VariantRead]:
    filters = ListFilters(status=status, language=language, topic=topic, platform=platform, strategy=strategy, created_at=created_at)
    items, total = list_models(db, GeneratedVariant, filters, limit, offset)
    return PaginatedResponse[VariantRead](items=items, limit=limit, offset=offset, total=total)


@router.get("/{item_id}", response_model=VariantRead, summary="Get variant")
def get_variant(item_id: int, db: Session = Depends(get_db)) -> VariantRead:
    return get_model_or_404(db, GeneratedVariant, item_id, "Variant")


@router.post("/{variant_id}/approve", response_model=VariantRead, summary="Approve variant")
def approve_variant(variant_id: int, approved_by: str = Body(default="api", embed=True), db: Session = Depends(get_db)) -> VariantRead:
    item = get_model_or_404(db, GeneratedVariant, variant_id, "Variant")
    item.status = Status.approved.value
    item.approved_at = now_utc()
    item.approved_by = approved_by
    db.add(ModerationAudit(variant_id=item.id, status=Status.approved.value, reviewer=approved_by, language=item.language, topic=item.topic, platform=item.platform, strategy=item.strategy))
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.post("/{variant_id}/reject", response_model=VariantRead, summary="Reject variant")
def reject_variant(variant_id: int, reason: str | None = Body(default=None, embed=True), rejected_by: str = Body(default="api", embed=True), db: Session = Depends(get_db)) -> VariantRead:
    item = get_model_or_404(db, GeneratedVariant, variant_id, "Variant")
    item.status = Status.rejected.value
    db.add(ModerationAudit(variant_id=item.id, status=Status.rejected.value, reviewer=rejected_by, comment=reason, language=item.language, topic=item.topic, platform=item.platform, strategy=item.strategy))
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.post("", response_model=VariantRead, status_code=status.HTTP_201_CREATED, summary="Create variant")
def create_variant(payload: VariantCreate, db: Session = Depends(get_db)) -> VariantRead:
    item = GeneratedVariant(**_model_data(payload))
    db.add(item)
    commit_or_rollback(db)
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=VariantRead, summary="Update variant")
def update_variant(item_id: int, payload: VariantCreate, db: Session = Depends(get_db)) -> VariantRead:
    item = get_model_or_404(db, GeneratedVariant, item_id, "Variant")
    for key, value in _model_data(payload, exclude_unset=True).items():
        setattr(item, key, value)
    commit_or_rollback(db)
    db.refresh(item)
    return item
